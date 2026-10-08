#!/usr/bin/env bash
# 本地真实 embedding 开发模式启动器（experiment/local-qwen3-embedding 分支专用）。
#
# 做什么：
#   1. 检查本机 Ollama、qwen3-embedding:0.6b 以及 /v1/embeddings 是否可用（维度必须 1024）
#   2. 用一套与 Docker 默认部署完全隔离的配置，在宿主机启动同一个 app（uvicorn app.main:app）
#      独立 Chroma 目录 / 独立 collection / 独立 SQLite，首次运行时自动 ingest 知识库
#   3. 只在本地监听（127.0.0.1），方便和仍在运行的 Docker 栈并存
#
# 不做什么（硬约束，脚本里有守护检查）：
#   - 不修改仓库根目录的 .env，也从不打印任何 API key
#   - 不写 Docker 默认数据目录 data/runtime（向量库和 SQLite 都不行）
#   - 不碰 docker-compose.yml，不把 Ollama 塞进容器
#   - 不改默认部署的 embedding provider（main 上仍然是 mock）
#
# 用法：
#   ./scripts/run-local-real-embedding.sh
#   可选：cp .env.local.example .env.local（存在则其中的值优先于脚本内置默认）
#   可覆盖：LOCAL_REAL_EMBEDDING_PORT / EMBEDDING_MODEL / OLLAMA_BASE_URL 等
#
# 停止：Ctrl-C（脚本会一并回收 uvicorn 子进程）
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

log() { printf '[local-real-embedding] %s\n' "$*"; }
die() { printf '[local-real-embedding] 错误：%s\n' "$*" >&2; exit 1; }

PORT="${LOCAL_REAL_EMBEDDING_PORT:-8001}"
RUNTIME_DIR="${LOCAL_REAL_EMBEDDING_DIR:-$REPO_ROOT/data/local-real-embedding}"
EMBEDDING_DIM="${LOCAL_REAL_EMBEDDING_DIM:-1024}"
OLLAMA_BASE_URL_DEFAULT="http://127.0.0.1:11434/v1"
# demo-admin-token 是 app/auth/auth.py 里的公开演示常量（README/DEMO_SCRIPT 均已写明），不是密钥
DEMO_ADMIN_TOKEN="${DEMO_ADMIN_TOKEN:-demo-admin-token}"

# --- 0. 可选读取 .env.local（只读，不写；用户值优先） ---
if [[ -f .env.local ]]; then
  log "发现 .env.local，使用其中的本地配置"
  set -a
  # shellcheck disable=SC1091
  source ./.env.local
  set +a
fi

OLLAMA_BASE_URL="${EMBEDDING_BASE_URL:-${OLLAMA_BASE_URL:-$OLLAMA_BASE_URL_DEFAULT}}"
EMBEDDING_MODEL="${EMBEDDING_MODEL:-qwen3-embedding:0.6b}"
CHROMA_PATH="${CHROMA_PATH:-$RUNTIME_DIR/chroma}"
CHROMA_COLLECTION="${CHROMA_COLLECTION:-hengguang_knowledge_qwen3}"
DATABASE_URL="${DATABASE_URL:-sqlite:///$RUNTIME_DIR/app.db}"
RAG_TOP_K="${RAG_TOP_K:-5}"
RAG_MIN_SCORE="${RAG_MIN_SCORE:-0.15}"

# --- 1. Ollama 已安装 ---
command -v ollama >/dev/null 2>&1 || die "未找到 ollama 命令，请先安装 Ollama（https://ollama.com）"
log "Ollama CLI：$(ollama --version 2>/dev/null | head -1)"

# --- 2. 目标 embedding 模型已拉取 ---
if ! ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$EMBEDDING_MODEL"; then
  die "本机没有 $EMBEDDING_MODEL，请先执行：ollama pull $EMBEDDING_MODEL"
fi
log "embedding 模型：$EMBEDDING_MODEL 已就位"

# --- 3. /v1/embeddings 可用，且维度和 collection 要求一致 ---
command -v curl >/dev/null 2>&1 || die "需要 curl 做本地探测"
if ! DIM="$(curl -fsS -m 30 "$OLLAMA_BASE_URL/embeddings" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"$EMBEDDING_MODEL\",\"input\":[\"dimension probe\"]}" \
  | uv run python -c 'import json,sys; print(len(json.load(sys.stdin)["data"][0]["embedding"]))' 2>/dev/null)"; then
  die "调用 $OLLAMA_BASE_URL/embeddings 失败，请确认 Ollama 已启动（ollama serve）且已开启 OpenAI 兼容层"
fi
if [[ "$DIM" != "$EMBEDDING_DIM" ]]; then
  die "向量维度不符：期望 $EMBEDDING_DIM，实际 $DIM。维度不匹配不能复用已有 collection"
fi
log "Ollama embeddings 正常：$OLLAMA_BASE_URL · 维度 $DIM"

# --- 4. ModelScope key（只取用，绝不打印；顺序：已导出 → 仓库 .env → 交互输入） ---
KEY_SOURCE=""
if [[ -n "${LLM_API_KEY:-}" ]]; then
  KEY_SOURCE="环境变量 LLM_API_KEY"
elif [[ -n "${MODELSCOPE_API_KEY:-}" ]]; then
  LLM_API_KEY="$MODELSCOPE_API_KEY"
  KEY_SOURCE="环境变量 MODELSCOPE_API_KEY"
elif [[ -f .env ]] && [[ -n "$(sed -n 's/^LLM_API_KEY=//p' .env | head -1)" ]]; then
  LLM_API_KEY="$(sed -n 's/^LLM_API_KEY=//p' .env | head -1)"
  KEY_SOURCE="仓库 .env 的 LLM_API_KEY（只读取，未打印）"
fi
if [[ -z "${LLM_API_KEY:-}" ]]; then
  if [[ -t 0 ]]; then
    read -rsp "请输入 ModelScope API Key（不回显、不打印）: " LLM_API_KEY
    printf '\n' >&2
    KEY_SOURCE="交互输入"
  else
    die "缺少 ModelScope key：请 export MODELSCOPE_API_KEY=... 或在仓库 .env 中设置 LLM_API_KEY=<key>"
  fi
fi
export LLM_API_KEY
log "LLM key 就绪（来源：$KEY_SOURCE，值不打印）"

# --- 5. 隔离守护：本地模式绝不能落到 Docker 默认数据上 ---
case "$CHROMA_PATH" in
  */data/runtime/chroma*)
    die "CHROMA_PATH=$CHROMA_PATH 指向 Docker 默认向量库，会和 mock collection 混写；请使用独立目录"
    ;;
esac
case "$DATABASE_URL" in
  *data/runtime/app.db*)
    die "DATABASE_URL 指向 Docker 默认 SQLite，两个进程争抢同一个库（实测 database is locked）"
    ;;
esac
if [[ "$CHROMA_COLLECTION" == "hengguang_knowledge" ]]; then
  die "CHROMA_COLLECTION 不能复用默认的 hengguang_knowledge：mock 与 Qwen3 向量空间互不兼容"
fi
if [[ "${EMBEDDING_PROVIDER:-ollama}" == "mock" ]]; then
  die "本脚本用于真实 embedding，EMBEDDING_PROVIDER=mock 请改用 docker compose up"
fi
mkdir -p "$CHROMA_PATH"
log "隔离配置：collection=$CHROMA_COLLECTION · chroma=$CHROMA_PATH · db=$DATABASE_URL"

# --- 6. 端口占用检查（避免和一个已在跑的实例混淆） ---
if curl -fsS -m 2 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  die "端口 $PORT 上已有健康的 API 实例；请复用它的 request_id，或用 LOCAL_REAL_EMBEDDING_PORT 换端口"
fi

# --- 7. 启动同一个 app（宿主机、仅本地监听） ---
log "启动 uvicorn app.main:app → http://127.0.0.1:$PORT"
LLM_PROVIDER="${LLM_PROVIDER:-modelscope}" \
LLM_BASE_URL="${LLM_BASE_URL:-https://api-inference.modelscope.cn/v1}" \
LLM_MODEL="${LLM_MODEL:-Qwen/Qwen3.8-Flash-Next}" \
LLM_FALLBACK="${LLM_FALLBACK:-false}" \
EMBEDDING_PROVIDER="ollama" \
EMBEDDING_BASE_URL="$OLLAMA_BASE_URL" \
EMBEDDING_API_KEY="${EMBEDDING_API_KEY:-ollama}" \
EMBEDDING_MODEL="$EMBEDDING_MODEL" \
CHROMA_PATH="$CHROMA_PATH" \
CHROMA_COLLECTION="$CHROMA_COLLECTION" \
DATABASE_URL="$DATABASE_URL" \
DOCUMENTS_DIR="${DOCUMENTS_DIR:-$REPO_ROOT/data/documents}" \
RAG_TOP_K="$RAG_TOP_K" \
RAG_MIN_SCORE="$RAG_MIN_SCORE" \
LOG_LEVEL="${LOG_LEVEL:-INFO}" \
LOG_JSON="${LOG_JSON:-false}" \
  uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

# --- 8. 等健康检查 ---
log "等待 /health（最多 120s，首次建库会慢一些）"
READY=0
for _ in $(seq 1 40); do
  if curl -fsS -m 3 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    die "uvicorn 进程已退出，请看上面的日志"
  fi
  sleep 3
done
if [[ "$READY" != "1" ]]; then
  die "等待 /health 超时"
fi
log "/health OK"

# --- 9. 独立 collection 首次使用时灌知识库（幂等，重复运行不会重复灌） ---
DOC_COUNT="$(curl -fsS -m 30 -H "Authorization: Bearer $DEMO_ADMIN_TOKEN" \
  "http://127.0.0.1:$PORT/api/knowledge/documents" \
  | uv run python -c 'import json,sys; print(len(json.load(sys.stdin)["documents"]))')"
if [[ "$DOC_COUNT" == "0" ]]; then
  log "独立 collection 为空，执行首次 ingest（真实 embedding，45 chunk → 约 3s）"
  # POST /api/knowledge/ingest 的请求体是必填的（字段全可选，所以发 {}）
  INGEST_RAW="$(curl -sS -m 600 -w '\n%{http_code}' -X POST \
    "http://127.0.0.1:$PORT/api/knowledge/ingest" \
    -H "Authorization: Bearer $DEMO_ADMIN_TOKEN" \
    -H 'Content-Type: application/json' -d '{}')"
  INGEST_CODE="$(printf '%s\n' "$INGEST_RAW" | tail -1)"
  INGEST_BODY="$(printf '%s\n' "$INGEST_RAW" | sed '$d')"
  if [[ "$INGEST_CODE" != "200" ]]; then
    die "首次 ingest 失败 HTTP $INGEST_CODE：${INGEST_BODY:0:300}"
  fi
  printf '%s' "$INGEST_BODY" | uv run python -c \
'import json,sys; d=json.load(sys.stdin); print("ingest status=%s documents=%s chunks=%s errors=%s skipped=%s" % (d["status"], d["documents"], d["chunks"], len(d["errors"]), len(d["skipped"])))'
else
  log "知识库已有 $DOC_COUNT 篇文档（跳过 ingest；需重建请删除 $CHROMA_PATH 后重跑）"
fi

log "就绪：http://127.0.0.1:$PORT"
log "  embedding=$EMBEDDING_MODEL · collection=$CHROMA_COLLECTION · RAG_MIN_SCORE=$RAG_MIN_SCORE · RAG_TOP_K=$RAG_TOP_K"
log "  自检：curl -s http://127.0.0.1:$PORT/api/models -H 'Authorization: Bearer $DEMO_ADMIN_TOKEN'"
log "  停止：Ctrl-C（Docker 栈 :8000/:3000 不受影响）"
wait "$SERVER_PID"
