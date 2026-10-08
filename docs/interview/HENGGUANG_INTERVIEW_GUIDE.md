# 恒光 AI 平台工程师 · 面试题库与项目标准答案

> **Hengguang AI Platform Engineer — Interview Preparation**
> 项目：`hengguang-ai-platform-demo` ｜ **代码证据基线（Code evidence baseline）：`460a6ee`**（Day 1–5 + Audit Fix）｜ 测试：**423 passed**（main HEAD 复跑）
> **文档基线：最终一致性修复提交**（本行之后新增的提交）。代码事实一律以 `460a6ee` 为准并保留该锚点；文档与测试计数以本轮修复后的工作树为准。`460a6ee` **不是当前 HEAD**，它是代码证据锚点。
> 本文件是唯一 canonical source；`index.html` 由它生成，不承载独立内容。
> 信息检索/整理时间：**2026-10-01**。所有可能变化的事实都带时间标记。

**标签约定（全文强制，不得混用）**

| 标签 | 含义 |
|---|---|
| `[FACT]` | 公开资料明确说明的事实（附来源与时间） |
| `[INFERENCE]` | 基于公开资料 + 岗位 JD 做的合理推断，**不是公司事实** |
| `[MY DESIGN]` | 我在本 Demo 中真实采用的方案（可在代码/测试中验证） |
| `[PRODUCTION NEXT]` | 如果进入真实生产环境，我下一步会做的事（建议，不是现状） |
| `[需要本人确认]` | 涉及本人经历/HR 信息，资料中不代填 |

---

# 0 · 使用方式

## 0.1 三种复习路径

| 场景 | 时间 | 看什么 |
|---|---|---|
| **快速复习**（面试当天早上 / 候场时） | 15 分钟 | §31 快速复习表 → §27 项目证据 → §23 最容易被质疑的 9 题 → §1 60 秒自我介绍 |
| **深度复习**（面试前 1–2 晚） | 90–120 分钟 | §4 项目介绍 → §5–§10 六大技术域 → §14–§20 平台能力 → §21 审查修复 → §26 系统设计 |
| **模拟面试**（找人或 self-talk） | 45 分钟 | 只做 `核心题`（完整 Short/Standard/Deep Dive 格式）：让对方从 §5/§6/§7/§8/§9/§14/§15/§21 里随机抽 8 题，每题严格 2 分钟，然后回答对方的 2 个追问 |

**答案长度分级**（本文件的每一道题都按这三档之一写）：

- `Short Answer`：30 秒内说完，1–3 句。用于打断自己啰嗦的倾向。
- `Standard Answer`：约 1 分钟，3–6 句 + 一句项目证据。默认面试就用这一档。
- `Deep Dive`：2–3 分钟，只有面试官继续追问时才展开；结构固定为「为什么这么做 → 怎么实现的 → 边界在哪 → 生产怎么升级」。

## 0.2 三条硬性纪律

1. **不夸大。** 这是一个求职 Demo，不是生产系统。所有回答允许出现的最高级表述是「在这个 Demo 里我做到了 X」，不允许「生产环境我们已经 X」。
2. **不编造经历。** `[需要本人确认]` 的位置必须由本人填真实信息；不知道就说不知道（§24 有专门答案模板）。
3. **不把推断说成公司事实。** 涉及恒光内部系统、正在做的 AI 项目、内部数据：一律 `[INFERENCE]` + 「这是我根据公开资料和 JD 做的技术推演」。

## 0.3 HTML 复习台用法

`docs/interview/index.html`（浏览器直接打开，无网络依赖）：

- 顶部搜索：跨全部题目做关键词过滤；
- `Category filter`：只看某一个技术域（RAG / Agent / RBAC …）；
- `Question only`：隐藏说明性章节，只看问答；
- `Expand all` / `Collapse all`：控制题目正文；
- 默认：**题目与 Standard Answer 展开，Deep Dive 折叠**（点开才看），避免复习时一次灌太多；
- 绿色区块 = `我的项目证据`（可直接指着代码/测试说）；红色区块 = `不要这样回答`。

---

# 1 · 我的 60 秒自我介绍

> `[需要本人确认]`：姓名、学历/专业/毕业年份、工作年限与雇主、现居地、GitHub 链接。
> 下面三版按「只依赖本仓库可验证事实」写，把 `[...]` 替换成真实信息即可直接使用。

## Q1-01 30 秒版（技术面开场）

#### Answer

面试官好，我是 `[姓名]`，`[X 年 Python 后端 / 学历专业，需要本人确认]`。
这一两年我把重心放在**企业级 LLM 应用的平台层**上：为了准备贵司这个岗位，我独立做了一个可运行、可 Docker 部署的最小企业 AI 平台原型——统一 Model Gateway、带引用的 RAG、白名单 Tool 的 Agent Runtime，外面套上 RBAC、审计、指标和错误信封，**423 个测试全部离线可跑**。
我今天想聊的主要就是这套东西为什么这么设计，以及哪些地方我还没做。

## Q1-02 60 秒版（标准）

#### Answer

面试官好，我是 `[姓名]`，`[学历/专业/年限，需要本人确认]`。

我的工程主线是 **Python 后端 + 可交付的平台层代码**：FastAPI、Pydantic 契约、SQLAlchemy、Docker Compose，以及把测试当作交付的一部分——我目前这个项目是 423 个测试（291 单元 + 132 集成），`ruff` 和 `tsc` 都是干净的。

第二条主线是 **LLM 应用工程**。我做了一个面向化工企业的求职原型：`hengguang-ai-platform-demo`。它想验证的不是「能不能聊天」，而是**模型、知识库、业务系统、Agent 能不能收敛进同一个平台层**，并且在这一层把权限、审计、失败处理做对。具体是四件事：所有模型访问只走一个 Model Gateway（provider 可切换、fallback 显式关闭、降级要打标）；RAG 用公开资料做 heading 感知分块 + 混合检索，回答必须带 `[n]` 引用，没依据时明确说「没有足够信息」；Agent 是一个有限步 loop，只能看到 4 个白名单工具，工具参数由 Pydantic 校验，业务查询只有固定 operation + 参数化 SQL；权限在路由和 `ToolExecutor` 两处都检查，越权是受控 `PERMISSION_DENIED` 而不是 500。

第三条是**自我纠偏**。项目做完我做了一次完整 code review，发现 5 个真实缺陷——错误路径漏审计、静默降级、401 响应泄露演示 token、工具 RBAC fail-open、审计内存无界——全部改掉并补了测试。

我申请 AI 平台工程师，是因为这个岗位正好把这三条合成一件事：从 0 到 1 把平台搭出来，还要自己运维它。`[如被问到岗/地点/薪资，见 §3。]`

## Q1-03 90 秒版（HR 面 / 交叉面）

#### Answer

（在 60 秒版前后各加一段。）

**开头加（15 秒 · 动机）**：
我先说结论：我是主动选择「企业 AI 平台」这个方向的，不是从别的方向没过才转过来。我的判断是——模型能力本身越来越像基础设施，真正难、也真正有价值的，是把它接进一家制造企业的权限、数据、审计和运维里。

**结尾加（15 秒 · 为什么是恒光 + 自我认知）**：
为什么投恒光：JD 写的是私有化 AI 平台从 0 到 1、模型网关、RAG、Agent、ERP/OA 集成、运维监控、模型评测与切换——这九件事几乎就是我这个 Demo 的目录结构，而它同时要求服务一个化工场景，这是我想要的那种「工程约束真实存在」的环境。
同时我也很清楚我的边界：这个项目用的是公开资料 + 合成数据，身份是三个演示 token，数据库是 SQLite。我没做过化工行业的生产系统，也不认为这个 Demo 可以直接上线。我能拿出的是一个已经跑通、已经自己审过一遍、并且讲得清每一步取舍的起点。

#### My Project Evidence

- 423 tests（`uv run pytest -q`）：291 unit + 132 integration
- Model Gateway：`app/gateway/base.py`、`app/gateway/router.py`、`app/gateway/openai_compatible.py`、`app/gateway/mock.py`
- RAG：`app/rag/chunker.py`、`app/rag/retriever.py`、`app/rag/prompt.py`、`app/rag/store.py`
- Agent：`app/agent/runtime.py`、`app/agent/executor.py`、`app/agent/registry.py`、`app/agent/tools/`
- RBAC / Audit / Metrics：`app/auth/`、`app/observability/`
- 审查修复：`git show 460a6ee`
- Docker：`docker-compose.yml`、`docker/api.Dockerfile`、`web/Dockerfile`

#### Follow-up Questions

- 你说的「平台层」具体指哪些代码？
- 这些测试都在测什么？会不会是自说自话？
- 你一个人做完这些用了多久？怎么安排的？
- 你哪里最没把握？

#### Pitfalls

- 不要说「我精通 / 我非常热爱 / 我一定能胜任」。
- 不要把「读过 Dify、LangChain 文档」说成「用过」。
- 不要在自我介绍里讲超过 10 秒的技术细节——那是后面 §4/§5 的事。
- 不要编造雇主、项目规模、上线结果。

#### Interview Keywords

`Python` `FastAPI` `Model Gateway` `RAG + citation` `Agent Tool Calling` `RBAC/Audit`

---

# 2 · 为什么应聘恒光 AI 平台工程师

> 岗位 JD（公开招聘信息快照，检索时间 2026-10-01，来源见文末 §来源）：`[FACT]`
> 职位「AI 平台工程师」，湖南恒光科技股份有限公司，衡阳（石鼓区），本科，招 1 人，8千–1.2万；
> 职责：① 私有化 AI 平台技术选型/架构设计/从 0 到 1 搭建（模型网关、知识库/RAG、Agent 工作流、内部系统集成）；
> ② 持续研究开源 LLM 应用生态（Dify、RAGFlow、FastGPT、One-API/New-API、MCP 协议等）并评估引入；
> ③ 完成平台与内部系统（ERP、OA 等）对接，保障数据安全与流程自动化；
> ④ 平台日常运维、监控、性能优化与故障处理；
> ⑤ 跟进各类大模型（国内外闭源/开源）接入、评测与切换，结合成本和效果优化选型；
> ⑥ 编写技术文档、沉淀平台使用规范，培训支持内部业务部门使用 AI 平台。
> 任职要求（可见部分）：计算机/软件工程相关本科（条件优秀者可放宽）；扎实编程基础（Python/Go/Node.js 任一）+ Docker、Linux 服务器部署运维经验；对大模型、AI Agent、… `[FACT 截断：JD 原文剩余条目面试前需以官方发布为准]`
>
> 由这份 JD 可以做的合理判断（**不是公司事实**）：`[INFERENCE]`
> 平台是从 0 到 1、单人起建、要自己选型并自己运维，且要面向内部业务部门做文档与培训。

## Q2-01 为什么想做 AI 平台？

#### Short Answer

因为我认为模型本身越来越像基础设施，稀缺的是把它变成企业内部可交付能力的那一层：网关、检索、工具、权限、审计、运维。我做的这个 Demo 就是这一层的最小版本。

#### Standard Answer

我的判断是这样：调模型 API 的门槛已经很低了，但企业里让模型「能用」的门槛不在 prompt，在四件事——数据能不能进模型（权限和脱敏）、回答能不能追溯（引用和审计）、动作会不会失控（工具白名单和边界）、服务挂了怎么发现（指标和日志）。这四件事都是平台层的工作。

所以我干脆按平台的形状做了这个项目：业务代码不允许 import provider SDK，只允许走 `ModelGateway`；工具只允许走白名单 `ToolRegistry`，参数由 Pydantic 校验；权限在路由和 `ToolExecutor` 两层各查一次；一次请求用一个 `request_id` 从 HTTP 追到工具调用。我没有用 LangChain/Dify，是为了让每一层的边界都是我亲手定的、能讲清楚的。

`[PRODUCTION NEXT]` 真平台上我下一步会补的是：多租户与配额、成本归因、模型评测流水线、以及身份接入（JWT/SSO），因为这个岗位 JD 里「运维 + 评测 + 切换」这三件事都需要它们。

#### My Project Evidence

- 强制单一入口：`app/gateway/router.py`（`ModelGateway.chat` 是唯一模型出口）
- 工具白名单：`app/agent/registry.py`（重名报错、未知工具报错）+ `app/agent/tools/__init__.py`（`build_default_registry` 只有 4 个工具）
- 双层权限：`app/auth/dependencies.py::require` + `app/agent/executor.py::ToolExecutor._execute`
- 一处关联：`app/observability/middleware.py`（`X-Request-ID` → `Actor.request_id` → 审计）

#### Follow-up Questions

- 你说平台层重要，那平台层和业务层怎么划界？谁来决定 prompt？
- 如果业务部门自己用 Dify 搭了一个应用，你这个平台还有什么价值？
- 平台做到什么程度算「可以交给别人用」？

#### Pitfalls

- 不要说「因为平台更有技术含量/更容易涨薪」。
- 不要贬低应用层：正确说法是「应用层要有快速交付的工具，平台层负责让它跑得安全、可审计、可换模型」。
- 不要把「我做了个 Demo」说成「我做过一个平台」。

#### Interview Keywords

`single choke point` `capability layer` `governance` `auditability`

---

## Q2-02 为什么想来制造业 / 化工企业做 AI？

#### Short Answer

因为这里的问题是真问题：数据不能出去、动作不能失控、结论要能追溯。这些约束会逼着工程做扎实，而不是做一个演示品。

#### Standard Answer

`[FACT]` 公开资料显示，恒光是围绕循环经济、集硫化工与氯化工产品链研发生产于一体的高新技术企业（2021-11-18 深交所创业板上市，代码 301118）；怀化基地在推进「工业互联网 + 危化安全生产」与智慧工厂平台建设。
`[INFERENCE]` 如果这些公开方向成立，那么这家企业手里已经不缺「数据」和「系统」，缺的是把它们变成人能问、能查、能追溯的能力——这正好是 AI 平台层的活。

我看重两点。第一，**知识密度高、且高度文档化**：操作规程、安全制度、设备手册、事故报告，这些是 RAG 最合适的语料，做出来立刻有人用。第二，**失败代价高**：这逼着我在设计第一天就把引用、审计、权限、边界写进去，而不是等出事再补。我的项目里 AI 只做检索、分析、解释、辅助决策，不做任何控制动作，就是这个约束的直接结果。

#### Follow-up Questions

- 化工企业和互联网企业做 AI 平台，最大的三个差别是什么？
- 你没有工艺背景，怎么和业务方对话？
- 你觉得第一个能落地见效的场景是什么？

#### Pitfalls

- 不要说「化工行业很酷 / 我从小就对化学感兴趣」这类空话。
- 不要暗示「AI 能优化生产、提升收率」，那是需要工艺人员验证的领域结论，`[INFERENCE]` 都不能替公司下。
- 不要说「互联网的行业知识不值钱」。

#### Interview Keywords

`domain constraints` `dense internal docs` `high cost of failure` `decision support only`

---

## Q2-03 为什么不是纯互联网 AI 应用？

#### Short Answer

互联网场景的 AI 应用大多在拼体验和增长，我更想做拼正确性和边界的那一类：可追溯、可控、私有化。我这项目就是按这一类做的。

#### Standard Answer

我理解的差别是失败模式：互联网 AI 应用答错一次，代价是一次糟糕的用户体验；企业内部 AI 答错一次或越权一次，代价可能是一条错误的处置建议、一次不该发生的数据外泄。所以后者的工程重点必然是引用、权限、审计、评测、灰度，而不是 prompt 的花样。

从纯工程角度我也更吃这一套：`[MY DESIGN]` 我的 RAG 在没有依据时明确回答「当前知识库没有足够信息」；`ToolExecutor` 在未认证或越权时返回结构化 `PERMISSION_DENIED` 而不是让 Agent 崩；`ModelGateway` 的 fallback 默认关闭，因为静默降级会让运维看不见。这些设计在互联网 demo 里几乎不被需要，在企业平台上是底线。

`[INFERENCE]` 顺带说一句：这类岗位在制造业里通常还是「少数人做很多事」——从选型到运维到培训。JD 里六条职责横跨架构、集成、运维、评测和文档，我对这一点是有意选择的，不是没意识到。

#### Follow-up Questions

- 如果给你两个选择：一个互联网大用户量 AI 应用 vs 我们这种内部平台，你怎么选？为什么？
- 你能接受日常有相当比例是运维和答疑吗？

#### Pitfalls

- 不要说「互联网太卷 / 互联网没前途」。
- 不要把「稳定 / 离家近 / 不加班」当作主要理由（可以放在 HR 面里轻描淡写，别放技术面）。

#### Interview Keywords

`correctness over polish` `traceability` `private deployment` `broad ownership`

---

## Q2-04 为什么认为这个岗位适合你？

#### Short Answer

JD 的六条职责，我这个项目逐条都碰过：模型网关、RAG、Agent 工作流、内部系统对接、运维与可观测、模型评测与切换。差别是我碰的是合成数据 + 演示凭据的最小版本，不是生产版本。

#### Standard Answer

我把 JD 逐条对了一遍（下表是口述版）：
模型网关 → `app/gateway/`；RAG/知识库 → `app/rag/`（分块、embedding、Chroma、citation、无依据拒答）；Agent 工作流 → `app/agent/`（loop、trace、`max_steps=5`/`max_tool_calls=8`）；内部系统集成 → `app/agent/tools/erp.py` + `app/db/queries.py`（白名单 operation + 参数化 SQL）；运维监控 → `GET /health`、`GET /metrics`、结构化 JSON 日志、`X-Request-ID`、Docker Compose 部署与重启持久化；模型评测与切换 → 换 provider 只改环境变量，真实模型冒烟已做。

我能补上的是**工程习惯**：423 个测试、code review 后自己找出并修掉 5 个缺陷、README/ARCHITECTURE/DEMO_SCRIPT 都写。
我要补上的是**生产经验**：真实身份体系、多租户、配额与成本治理、私有推理（vLLM/Ollama）的容量与并发调优、面向业务部门的支持流程。这些我准备在 §22 里主动交代，而不是等被问。

**JD 对照表（可直接背）**

| JD 职责 | 我的对应实现 | 成熟度 |
|---|---|---|
| 模型网关 / 多模型接入与切换 | `ModelGateway` + `OpenAICompatibleProvider`（DeepSeek/Qwen/Ollama 同协议） | Demo 级：可切、可降级、可列表 |
| 知识库 / RAG | `chunker → embeddings → Chroma → retriever → citation`，无依据拒答 | Demo 级：6 篇公开文档 / 45 chunk |
| Agent 工作流 | `AgentRuntime` loop + `TraceStep` + 限制预算 + 受控失败 | Demo 级：单 Agent、无持久化会话 |
| 内部系统对接（ERP/OA） | `erp_purchase_analysis`（7 operation）/ `safety_incident_analysis`（5 operation） | **合成数据**，接口形状可复用 |
| 运维 / 监控 / 故障处理 | `/health` `/metrics` JSON 日志 统一错误信封 Docker Compose | 进程内指标，重启清零 |
| 模型评测 / 成本选型 | 配置化 provider、`degraded` 打标、可观测延迟 | 尚未建评测集（见 §22） |
| 技术文档 / 培训 | README / ARCHITECTURE / DEMO_SCRIPT（5–8 分钟演示脚本） | 面向「教会别人用」的形状 |

#### Follow-up Questions

- 这几条里你最没底的是哪一条？
- 平台评测你会怎么起步？
- 内部系统对接你第一步做什么？

#### Pitfalls

- 不要说「我全都符合要求」。要说「这几条我做到了最小版本，那两条我还没做过」。
- 不要把「研究了 Dify/RAGFlow 的文档」说成「我会用 Dify 做生产」——正确表述见 §10、§23。

#### Interview Keywords

`JD-to-code mapping` `honest gap list` `delivery habits`

---

## Q2-05 你没有化工行业经验，怎么办？

#### Short Answer

对，我没有。我的策略是：把工程这一半先做到可验证，行业那一半用可核查的方式补——公开年报、安全制度文本、以及入职后跟着 SOP 和现场的人问对问题。

#### Standard Answer

我会把这个问题拆成三层。
第一层，**行业知识（工艺、产品、法规）**：我确实没有。我不会假装懂氯碱或硫铁矿焙烧；我能做的是把公开资料读准——`[FACT]` 我整理知识语料时就读过公司公开简介、2021 招股与上市公告、2025 年报、2026 半年度报告的公开内容（截至 2026-10-01），所以「两环产品链、三大基地、循环经济」这层框架我清楚。
第二层，**方法论（怎么把不懂的领域变成可检索、可引用的系统）**：这是我这个项目练的东西。我的答案不是「我去学化工」，而是「我搭一个让 SOP 和制度文件变成可引用知识的管线」，然后让懂工艺的人来验收内容。
第三层，**边界意识（什么不该让 AI 做）**：这恰恰是外行更容易犯的错。所以我在 Demo 里把「AI 不做控制」写死在工具白名单里——只读查询，固定 operation，参数化 SQL。

`[PRODUCTION NEXT]` 如果我入职，前 60 天我给自己的任务是：读完安全环保与信息化的公开材料 + 公司制度模板，跟 HSE 与设备同事各做一轮访谈，交一份「哪些文档有权威版本、谁能批准入库、哪些字段绝对不能出现在日志里」的清单。这是平台工程师能独立交付、又不需要工艺判断力的第一件实事。

#### Follow-up Questions

- 你要怎么判断一份 SOP 是不是可以进知识库？
- 业务专家说「AI 这个回答不对」，你作为不懂工艺的工程师怎么处理？
- 你打算多久能上手？

#### Pitfalls

- 不要说「行业知识两周就能补上」——这是把人当外行。
- 不要说「化工其实主要就是流程管理，通用工程能力可以迁移」（听起来像在贬低专业壁垒）。
- 不要编造任何与化工相关的个人经历。`[需要本人确认]`

#### Interview Keywords

`know what I don't know` `content owner is the business` `hard safety boundary` `60-day plan`

---

# 3 · HR 面问题

> 说明：涉及本人真实经历、薪资、到岗、地点的条目一律留 `[需要本人确认]`，我不代为填写。
> HR 面纪律：诚实、简短、不批评前雇主、不透露他人隐私、不承诺没有权限承诺的事。

## Q3-01 请用 1–2 分钟介绍一下你自己。

#### Answer

用 §1 的 60 秒版即可（HR 面不要背技术细节，重点放在「学习路径 + 自我驱动 + 沟通」）。可以加一句：我习惯把做过的东西写成文档并讲给别人听——这个项目我写了 README、ARCHITECTURE 和一份 5–8 分钟的演示脚本（`DEMO_SCRIPT.md`），这是 JD 里「编写技术文档、培训支持业务部门」那条要求的最低成本练习。

## Q3-02 为什么从上一份工作离开 / 为什么换方向？

#### Answer

`[需要本人确认：上一份工作的真实离职原因]`
框架（替换成事实后再用）：
「上一份工作我主要做 `[事实]`。离开的原因是 `[事实：方向/成长/客观因素]`，不是人际或薪资冲突。换到 AI 平台方向不是临时起意：我从 `[时间]` 开始系统做这件事，方式是先把一个完整的最小平台自己跑通，再去找能落地的环境。」
禁止项：不说前公司坏话、不说「被裁所以随便看看」、不把「AI 火」当唯一理由。

## Q3-03 为什么是 AI？

#### Answer

因为这是我见到的第一个「工程约束多到能撑成一个岗位、而我又能在几个月内拿出可验证成果」的方向。我不是从算法/研究进入的，我从工程进入：接口契约、失败处理、权限、可观测、可复现测试。我认为企业内部 AI 平台缺的正是这种人。

## Q3-04 为什么是恒光？

#### Answer

三个理由：一，`[FACT]` JD 写的是私有化 AI 平台从 0 到 1，涵盖模型网关、RAG、Agent、内部系统集成、运维、模型评测——这正好是我这一年的练习方向；二，业务背景是化工，约束真实、失败代价高，平台层的能力会被真正需要；三，从 0 到 1 + 招 1 人 `[FACT 来自 JD]`，意味着交付面很宽（选型、开发、运维、文档、培训都要做），这对我是加速成长的位置。`[INFERENCE]` 我也清楚这代表支持资源可能有限，我是按这个前提来评估的。

## Q3-05 期望薪资？

#### Answer

`[需要本人确认：底线值 / 期望值 / 可接受区间]`
建议口径：「我看到岗位公开范围是 8–12K，我目前的期望是 `[区间]`，更愿意先看工作内容、职责边界和成长空间；如果平台方向和职责跟我理解的一致，区间可以谈。」
禁止项：虚报当前薪资、编造 offer。

## Q3-06 到岗时间？

#### Answer

`[需要本人确认]`。若在职：说明交接周期（法定提前 30 天通知，具体以合同为准）。若应届/待业：可说「确认 offer 后一周内」，不要说「随时」这种把自己估值归零的表述。

## Q3-07 工作地点 / 能否接受衡阳（或怀化基地）？

#### Answer

`[FACT]` JD 工作地点为衡阳石鼓区（公开快照）。
`[需要本人确认：现居地、通勤/搬迁可行性、家庭约束、是否接受驻场基地]`
建议口径：明确说能或不能，不要含糊。若需要出差到基地，主动问清频率。

## Q3-08 你的项目经验主要来自这个 Demo，你怎么看它的分量？

#### Answer

它是**能力证据**，不是**生产经验**。它能证明：我能在没有外部依赖的情况下把模型、检索、Agent、权限、审计、指标和部署做成一个跑通的整体（423 个测试，Docker 可部署），并且能审自己的代码（自己发现并修了 5 个缺陷）。它不能证明：我处理过多租户、真实 ERP 数据、线上事故和生产容量。我不会用第一件去冒充第二件。

## Q3-09 你最大的优点是什么？

#### Answer

「我能把一件没做完的事做成可运行的东西，并且知道它没做完的部分在哪。」举例：这个 Demo 我把限制逐条写进 README（演示 token、合成数据、SQLite、进程内指标、部分同步 IO、无真实 DCS/ERP），做完还专门写了一章「我还没做什么、生产化怎么升级」。我认为平台工程师这个岗位最怕的就是把「能跑」当成「能上线」。
`[需要本人确认：如需真实工作例证替换]`

## Q3-10 你的不足是什么？

#### Answer

三个真实的：
一，我没有生产系统的容量与故障处理经验——没有大规模并发、没有 GPU 推理服务运维、没有真实 SLA。我补的方式是先从「可观测 + 可回滚 + 有限预算」这种工程习惯做起，并主动跟有运维经验的同事学。
二，我没有化工行业知识，也没有和企业内部业务部门长期对接的经历。`[需要本人确认：是否有其他沟通经历]`
三，我倾向于先把边界做完整再往前推，有时会拖慢第一版的速度——我在项目里用「5 天分四步、每天必须有可运行结果」的方式逼自己控制范围。

## Q3-11 遇到困难 / 压力怎么办？

#### Answer

先把它变成可验证的小问题。具体习惯：把故障复现成一个失败测试（这一步会迫使你把「感觉不对」变成「这一行断言不对」），修完这个测试就永久留下回归保护——§21 那 5 个缺陷都是这个流程做的。
`[需要本人确认：如需一个真实工作中的压力事件作为主例，请替换]`

## Q3-12 如何学习陌生技术？

#### Answer

我的固定四步：① 先找它要解决的那一个具体问题；② 跑最小可运行示例，把它的输入输出打出来看；③ 读它的接口/类型定义（这是我理解设计意图最快的路径）；④ 用它写一个我自己需要的小东西，做完就忘也不亏，因为管线留下了。
举例：我学 MCP 的方式是先读 spec 的 overview（Host/Client/Server、Tools/Resources/Prompts），然后对照我自己项目里的 `ToolRegistry`，问「我的白名单工具如果换成 MCP 暴露，边界应该放在哪」——这个问题我至今没写完，但我已经知道怎么给方案。

## Q3-13 如何独立推进一个项目？

#### Answer

先写规格，再写代码。这个项目我第一天先写 `SPEC.md`：包括目标、明确禁止项（3–5 天不做 K8s/Kafka/Redis/微服务）、数据边界、验收标准，然后按 Day 1–5 排：网关 → RAG → Agent → 平台化 → 产品化，每天结束必须可运行。中途不改方向，超出范围的一律记到「下一步」，不进本期。

## Q3-14 能否接受做企业内部平台（用户是公司内部同事，不是海量用户）？

#### Answer

能，而且我认为这更适合我现在的阶段。内部平台的特点是：**用户可对话、需求可追、失败可复盘**，但用户也最不留情——答错两次就不用你了。所以我做这个项目时把「引用」和「审计」当作第一优先级，因为内部平台靠信任活着，不靠日活。
`[INFERENCE]` 我也理解这类岗位的日常会包含相当比例的答疑、数据口径核对和文档维护，这些我在 JD 第 6 条里看到了，我是有意接受的。

## Q3-15 能否接受从 0 到 1（没有前人交接、什么都要自己搭）？

#### Answer

能。`[FACT]` JD 明确写了从 0 到 1、且这个岗位招 1 人。我的准备方式是：把「0 到 1」拆成能验证的台阶——第一周先做一个只有一个知识库问答 + 一个模型网关的可运行版本，让有人能用；第二周补权限和审计；只有当它真的被人用起来了，我才加评测、路由、成本治理。我不会在第一个月就把架构图画成十个微服务。
我也想说清风险：0 到 1 的岗位最怕「技术上做完了但没人用」，所以我会把「谁验收、有没有真实用户、用不用得起来」当成排期的一部分，而不是交付之后才问。

## Q3-16 你还有其他面试 / offer 吗？

#### Answer

`[需要本人确认]`。建议口径：如实、简短，不用于抬价，不说「你们是我的保底」。

---

# 4 · 请介绍一下你的项目

> 这一节是全场核心。四种时长都写好了，按面试官给的时间选择，**不要越级**。

## Q4-01 30 秒版

#### Answer

这是我针对贵司 AI 平台岗做的一个可运行、可 Docker 部署的最小企业 AI 平台原型。它想验证的不是聊天机器人，而是模型、知识、业务系统和 Agent 能不能收敛进同一个平台层：所有模型调用走统一 Model Gateway，企业知识走带 `[n]` 引用的 RAG，Agent 只能用 4 个白名单工具查业务数据（固定 operation + 参数化 SQL），外面套 RBAC、审计、指标和统一错误结构。423 个测试离线可跑。知识库用公开资料，业务数据是合成的，不接任何内部系统。

## Q4-02 60 秒版（推荐：结构完整的最短版本）

#### Answer

**为什么做**：`[FACT]` 这个岗位要的是私有化 AI 平台从 0 到 1，包含模型网关、RAG、Agent、内部系统集成、运维和模型评测。我认为这类岗位真正的难点不在 prompt，在平台层：权限、审计、失败处理、可观测。
**解决什么**：所以我把这四件「不性感但决定能不能上线」的事，和一个能跑的 AI 应用一起做出来。
**架构**：Web Console（React + nginx 反代）→ FastAPI → 鉴权（Bearer → 角色 → 权限）→ Agent Runtime → 白名单工具（RAG 检索、文档元数据、ERP 采购、安全事件）→ 模型走 Model Gateway（mock 或任意 OpenAI-compatible），数据走 SQLite（合成）+ Chroma。横向是审计、指标、结构化日志和统一错误信封。
**关键技术**：provider 抽象与显式 fallback、heading 感知分块 + 混合检索 + citation、有限步 Agent loop、双层 RBAC、`request_id` 全链路贯穿。
**难点**：最难的不是功能，是把失败路径做对——越权不能 500、provider 挂了不能静默降级、审计不能把 prompt 和凭据写进去。
**测试与部署**：423 个测试（291 单元 + 132 集成），全离线；Docker Compose 起 API + Web，`/health` 做启动依赖，重启后 SQLite/Chroma 数据仍在；真实模型冒烟做过。
**限制**：演示 token 不是 JWT/SSO，SQLite 不是生产库，业务数据是合成的，AI 不接 DCS、不做控制。

## Q4-03 2 分钟版

#### Answer

（60 秒版全部 + 下面三段。）

**一、为什么自己搭而不用 Dify/LangChain。**
我想要的是「每个边界都是我自己定义的」。比如工具级权限：我要 RBAC 检查发生在 `ToolExecutor` 里，位置固定在参数校验和真实数据访问之前——`[MY DESIGN]` 这个决定如果我套现成框架，就得先理解它的数据结构和扩展点，反而更慢。同时我给自己留了个约束：我对外只暴露 OpenAI 兼容的 tool schema，也就是说我随时可以把这一层换成 MCP 或任意框架，而不动业务代码。Dify/RAGFlow 我读过文档、也认可能快速交付，但我无法向面试官解释「它为什么把权限放在那里」。这个项目我能。

**二、一次真实请求的完整链路。**
「最近 30 天主要原材料采购价格有什么变化？」→ 中间件生成 `req_<uuid4>`，写 `X-Request-ID`；`require(agent:run)` 通过；AgentRuntime 把 policy + 问题交给 ModelGateway；模型请求 `erp_purchase_analysis`；`ToolExecutor` 先查工具白名单、再查 `tool:erp` 权限（operator 在这里被拒并写一条 `denied` 审计）、再用 Pydantic 校验 `operation/days/limit`；工具把 operation 映射到 `queries.py` 里一段固定 SQL，参数绑定执行；结果同时产出两个视图——给模型的文本块和给平台的结构化 payload；模型基于工具结果生成最终回答；审计写入 `agent.run` + `tool.call`（同一 request_id），指标计数；前端渲染回答、trace 时间线、工具调用、引用。整条链我用一个 `request_id` 追得回来：`GET /api/audit/{request_id}`。

**三、我最想让人追问的地方。**
就是我做的那次 code review。它发现 5 个缺陷，其中两个是真安全问题：工具 RBAC 在 `actor=None` 时 fail-open，以及 401 响应体把演示 token 全列了出来。我修完都补了测试。我认为这比功能数量更能说明我像不像一个平台工程师。

## Q4-04 5 分钟版（对照 `DEMO_SCRIPT.md`，最好开屏演示）

#### Answer

**第 1 分钟 · 定位与边界（先说清楚，别让人误会）**
这是我针对贵司「AI 平台工程师」岗位做的求职原型，5 天分四步做完，现在是稳定的第 6 个提交。它不接任何内部系统、不用任何内部数据：知识库全部来自公开资料（公司简介、招股与上市公告、2025 年报、2026 半年报的公开摘要），ERP 和安全数据全部是按固定 seed 生成的合成数据。AI 在这里只做检索、分析、解释、辅助决策，不接 DCS、不做工业控制。
我想验证的命题是：**模型、知识、业务系统、Agent 能不能收敛进同一个 AI 平台层，并且在这一层把权限、审计、失败处理都做对。**

**第 2 分钟 · 架构 + 知识链路（可开 Dashboard 与 Knowledge 页）**
后端 FastAPI + Pydantic v2 + SQLAlchemy 2 + Chroma，包管理 uv；前端 React 18 + Vite + TS，无 UI 框架，nginx 静态托管并同源反代 `/api`、`/health`、`/metrics`。
模型侧：`app/gateway/` 是唯一的模型出口，`ModelProvider` 只是一个带 `async chat()` 的 Protocol，实现有 `MockProvider` 和 `OpenAICompatibleProvider`。业务代码不 import 任何 provider SDK。换 DeepSeek/Qwen/Ollama 只改环境变量；fallback 由 `LLM_FALLBACK` 显式打开（默认关），一旦降级，响应 `degraded=true`，审计与指标看得见。
知识侧：`data/documents/` 的 Markdown 带 front matter（document_id/title/source/url/published_at）→ heading 感知 chunker（1000 字、overlap 150，chunk 里带 section 路径）→ embedding（默认离线 hash-ngram mock，可切 OpenAI-compatible）→ Chroma 持久集合 → retriever 做向量 + 词面重合的融合打分，top_k=5，低于阈值直接丢弃 → prompt 里带上回答策略（只用资料、不编造、必须 `[n]` 引用、区分事实/推测/建议）。现在库里是 6 篇文档 / 45 个 chunk。
效果：有依据 → 回答带引用；无依据 → 明确说「当前知识库没有足够信息」。

**第 3 分钟 · Agent + 业务工具**
`POST /api/agent/run`。`AgentRuntime` 是一个有限步 loop：`max_steps=5`、`max_tool_calls=8`（可由配置和请求覆盖，请求侧上限 20 步）。每一步把消息和 4 个工具的 schema 交给网关；模型不带 tool_calls 就收尾，带就交给 `ToolExecutor`。`ToolExecutor` 顺序固定：**查工具白名单 → 查工具权限 → Pydantic 校验参数 → 执行**，任何异常都转成结构化 `ToolResult(success=false, error_code=…)`，loop 永远继续、HTTP 永远 200，不会把 500 甩给前端。
四个工具：`knowledge_search`（把 RAG 包成工具，citation 一路活到最终回答）、`document_lookup`（文档元数据）、`erp_purchase_analysis`（7 个固定 operation）、`safety_incident_analysis`（5 个固定 operation）。ERP 与安全工具走 `app/db/queries.py`：只有固定 SQL + 命名参数绑定，**模型没有能力传表名、列名或 SQL 片段**，参数越界被 Pydantic 拦成 `INVALID_ARGUMENTS`。每个工具的 payload 都自带 `data_source="data/synthetic"` 和「合成演示数据」的 disclaimer。
trace 是平台的一部分：`TraceStep` 记录每一步类型（llm / tool_call / final / stopped）、工具名、耗时、结果规模（如 `5 chunks` / `8 rows`）。

**第 4 分钟 · 平台层（RBAC / Audit / Metrics / 错误 / Docker / 测试）**
RBAC：Bearer → `CurrentUser` → 角色 → 权限，10 个权限、3 个角色（admin/manager/operator）。权限分两个**不互相继承**的家族：路由权限（`chat:run`、`audit:read`、`knowledge:ingest`、`users:manage`…）和工具权限（`tool:knowledge`/`tool:erp`/`tool:safety`）。`ToolExecutor` 里再查一次，是因为 Agent loop 会绕过路由；未认证或越权 → 结构化 `PERMISSION_DENIED` + 一条 `denied` 审计。未知角色一律归到最受限的 operator（fail-closed）。
审计与指标：同一个 `request_id` 贯穿日志与审计两层：`http.request` 只进结构化日志（并参与指标计数），`agent.run` / `tool.call` 与 API 行为落 `audit_logs` 表；只写紧凑摘要——`sanitize_summary` 用 denylist 把 prompt、messages、content、token、api_key 这类字段全部排除，嵌套结构只留长度，字符串截断 160 字符，最多 12 个 key。`GET /api/audit/{request_id}` 一条链查到底，这个端点本身也要 `audit:read`。指标是 15 个进程内计数器（请求/成功/错误/工具调用/工具失败/权限拒绝/Agent 运行按状态/审计写入/延迟均值与峰值/uptime），`GET /metrics` 输出 JSON，`GET /health` 输出状态与建库探针。错误统一 `{detail, request_id, error:{code,message,details}}`，不返回 traceback。
Docker 与测试：`docker compose up --build` 起 API（`python:3.11-slim` + `uv sync --frozen`，`/health` healthcheck）和 Web（`node:22-alpine` 构建 → `nginx:1.27-alpine`，`:3000`），`./data/runtime` 挂卷，`depends_on: service_healthy` 保证不 502；我验证过 stop/up 之后审计行数、Chroma 文档数、旧 request_id 的轨迹都还在。测试 420 个，`MockProvider` + `MockEmbeddingProvider` + 临时 SQLite/Chroma，零网络零 Key；其中 30 个是 Web Console 契约测试，钉死前端依赖的每个字段，防止后端字段漂移悄悄打断前端。

**第 5 分钟 · 我审过自己 + 限制 + 下一步（收尾）**
Code review 找到 5 个问题：错误路径漏审计、静默降级、401 泄露演示 token、工具 RBAC fail-open、审计内存无界。都修了并补了测试。
限制我逐条写进 README：身份是 3 个固定 token；SQLite + 单机 Chroma；指标重启清零；部分 async 端点里还有同步 IO；ERP/Safety 是合成数据；没有多租户、没有 K8s；真实 LLM 做过冒烟但不是常规测试依赖。
下一步按顺序：真实身份（JWT/SSO，权限矩阵和工具边界可整体保留）→ 共享存储与推理服务（Postgres + 向量服务 + 本地推理）→ 模型评测与成本路由 → 真实业务系统只读接入（先单接口、先白名单、先审计）→ 再谈 MCP 化与更多 Agent 能力。

#### Interview Keywords

`platform layer` `whitelist tool` `dual RBAC` `request_id` `423 tests` `synthetic only`

---

# 5 · 项目架构深挖

> 本节回答「为什么长这样」。每题都必须能落到当前代码上。

## Q5-01 为什么要单独分一层 Model Gateway？

#### Short Answer

为了让「换模型」是一个配置动作而不是一个代码改动，同时把失败处理、降级打标、模型目录这些平台职责收在一个点上。

#### Standard Answer

`[MY DESIGN]` 我把所有模型访问收在 `app/gateway/router.py::ModelGateway.chat`。业务代码（chat 端点、RAG pipeline、AgentRuntime）都只调它，不允许 import 任何 provider SDK；`app/gateway/base.py` 里的 `ModelProvider` 只是一个 `async chat()` 的 Protocol，实现侧 `MockProvider` 和 `OpenAICompatibleProvider` 各自继承 `BaseProvider`，`BaseProvider.chat` 先做入参校验（空 messages、temperature 越界直接 `ValueError`）再委派给 `_chat_impl`。
收益有三个：① provider 可换（DeepSeek/Qwen/Ollama 都走 OpenAI 兼容协议，只改 `LLM_PROVIDER/LLM_BASE_URL/LLM_MODEL`）；② 失败与降级只有一个决策点（`LLM_FALLBACK` 开关 + `degraded=true` 打标）；③ 测试可以完全离线（423 个测试全部走 mock，不依赖外部 Key）。
`[PRODUCTION NEXT]` 生产上我还会在同一层加：按模型的超时与重试预算、按用户/部门的限流与配额、token 与成本计量（现在 `usage` 已经从 provider 透传但没进指标）、按任务的路由策略与影子评测。

#### My Project Evidence

- `app/gateway/base.py`：`ModelProvider` Protocol、`BaseProvider` 校验骨架、`ModelResponse`（含 `degraded`）
- `app/gateway/router.py`：`_init_providers`（mock 恒在、真实 provider 需 base_url+api_key 才注册）、`get_provider`、`chat`
- `app/gateway/openai_compatible.py`：`httpx.AsyncClient` + `/chat/completions` + `parse_tool_calls`
- `tests/unit/test_gateway.py`：provider 注册、fallback 开关、`degraded` 打标

#### Follow-up Questions

- 网关会不会成为单点？你怎么避免它长成上帝类？
- 网关层怎么做超时、重试和幂等？
- 成本归因放在网关还是放在审计？

#### Pitfalls

- 不要说「为了微服务/解耦所以要有网关」——它现在就是一个库内的抽象层，不是独立服务，说成服务会被追问服务边界。
- 不要说「有了网关就不用改代码」——协议不兼容的 provider（比如只支持自家 messages 格式的）仍需要新 adapter。

#### Interview Keywords

`provider abstraction` `single choke point` `explicit fallback` `offline testability`

---

## Q5-02 Agent 为什么不直接调用模型 SDK？

#### Short Answer

因为一旦 Agent 直接 import SDK，权限、审计、降级、用量统计就会散落在每个调用点，平台层就没有「一处收口」了。

#### Standard Answer

`[MY DESIGN]` `AgentRuntime` 的构造签名是 `AgentRuntime(gateway, registry, config, audit)`——它拿到的 `gateway` 是 `ModelGateway` 类型，`tools` 来自 `ToolRegistry.openai_schemas()`。所以 Agent 里没有任何 provider 专属代码：`await self._gateway.chat(state.messages, tools=tools)`。这条规则的实际收益在 Day 5 的真实模型冒烟里体现得最直接：换 `LLM_PROVIDER=openai-compatible` 之后，同一条 Agent 链路（trace、citation、审计）一字未改就跑通了。
第二层理由是**测试形状**：我要能在单元测试里精确控制模型「这一步要不要调工具、调哪个工具」。`MockProvider` 接受一个 `script` 队列（元素是工具名或 `"final"`），这样我可以稳定地测 `max_steps`、`max_tool_calls`、工具失败、未知工具这些分支，而不是祈祷真模型配合我。
`[PRODUCTION NEXT]` 同一条规则我还会延伸到 embedding：`app/embeddings/` 用同一形状收口（`EmbeddingProvider` 抽象 + mock / OpenAI-compatible 两实现），所以 RAG 的向量出口也只有一处。

#### My Project Evidence

- `app/agent/runtime.py`（只依赖 `ModelGateway` / `ToolRegistry`）
- `app/gateway/mock.py::MockProvider.__init__(script=…)`（脚本化 loop 测试）
- `tests/unit/test_agent_runtime.py`、`tests/unit/test_agent_mock.py`
- `app/embeddings/base.py` + `app/embeddings/mock.py`

#### Follow-up Questions

- 那如果某个模型不支持 tool calling 怎么办？
- 网关这层你怎么做 A/B 或影子流量？
- Agent 的 prompt 归谁管？

#### Pitfalls

- 不要把这条说成「抽象是为了以后换框架」这种空泛理由——给出具体收益：一处收口 + 可测。
- 不要说「所以我们支持所有模型」——只支持 OpenAI 兼容协议，不兼容的必须写新 adapter，被问就承认。

#### Interview Keywords

`protocol dependency` `scripted mock` `no provider leak`

---

## Q5-03 Agent Runtime 怎么工作？

#### Short Answer

一个带预算的 while loop：每一步调模型，模型不带 tool_calls 就收尾，带就交给 ToolExecutor 执行并把结果作为 tool 消息回填；预算用尽就显式停止并留下 `stopped` trace。

#### Standard Answer

`[MY DESIGN]` 状态全部收在 `AgentState`：`messages / tool_calls / tool_results / sources / step / model / provider / final_answer / trace`。
一轮循环：
① 预算检查：`step >= max_steps` → `status=max_steps`；已执行工具数 `>= max_tool_calls` → `status=max_tool_calls`；
② `response = await gateway.chat(state.messages, tools=registry.openai_schemas())`，记一条 `TraceStep(type="llm", tool=<首个请求工具名>, latency_ms)`；
③ 若 `not response.tool_calls`：`final_answer = content`，记 `type="final"`，break；
④ 否则把响应转成 OpenAI 兼容的 assistant 消息（含 `tool_calls`）追加进 messages，逐个 `await executor.execute(call, actor=actor)`，结果转成 `role="tool"` 消息回填；工具的 `metadata["sources"]` 累加进 `state.sources`（citation 就是这样从 Chroma 一路活到最终回答的）；失败也回填，内容是「工具执行失败：…」，让模型有机会换路径；
⑤ 出 loop 后若还没有最终答案，生成一段明确的停止说明并记 `type="stopped"`。
默认 `max_steps=5`、`max_tool_calls=8`（`AGENT_MAX_STEPS`/`AGENT_MAX_TOOL_CALLS`），请求侧可覆盖 `max_steps`（1–20）。返回 `AgentRunResult`（answer/model/provider/steps/status/tool_calls/sources/trace/request_id），其中 `status ∈ {completed, max_steps, max_tool_calls}`。

#### My Project Evidence

- `app/agent/runtime.py`：loop、`_assistant_message`、`_tool_message`、`_result_detail`
- `app/agent/models.py`：`AgentState` / `TraceStep` / `AgentRunResult`
- `app/agent/prompts.py`：`AGENT_SYSTEM_PROMPT`（6 条策略：优先知识库、不编造、保留 `[n]` 引用、工具不是最终答案、不得假装调用不存在的工具）
- 测试：`tests/unit/test_agent_runtime.py`、`tests/integration/test_agent.py`

#### Follow-up Questions

- 多个 tool_call 是串行执行的，为什么不做并行？
- loop 没有记忆/持久化，重跑同一请求结果一样吗？
- 模型连续调用同一个无进展的工具怎么办？

#### Pitfalls

- 不要说「Agent 会自主规划」。我实现的是 tool-calling loop，规划能力来自模型；被追问「你的 planner 在哪」时不要顺着往上编。
- 不要说「状态可以随便重放」。我没有做 run 持久化/断点续跑，被问就承认。

#### Interview Keywords

`finite loop` `budget` `trace` `tool message` `status`

---

## Q5-04 Tool Registry 为什么需要白名单？

#### Short Answer

因为工具就是代码执行权限。白名单让「Agent 能做什么」变成一个可枚举、可审计、可在测试里钉死的事实，而不是模型或 prompt 决定的事。

#### Standard Answer

`[MY DESIGN]` `ToolRegistry` 只有四个方法：`register`（重名直接 `ValueError`）、`get`（未知工具直接 `KeyError`，不返回 None）、`list/names`、`openai_schemas()`。平台侧唯一的构造点在 `app/agent/tools/__init__.py::build_default_registry`，注册 4 个工具并写死 `DEFAULT_TOOL_NAMES`；`tests/integration/test_web_console_contract.py::test_tool_whitelist_is_the_four_shipped_tools` 把这个事实钉成测试——**加一个工具必须同时改代码和改测试**，这是有意的摩擦。
白名单还有第二个作用：**它是权限的挂载点**。每个 `Tool` 自带 `permission`（默认 `agent:run`，业务工具覆盖为 `tool:erp` / `tool:safety`），所以「这个工具要什么权限」写在工具自己身上，不是散在某个配置文件里。
另外 schema 也是单一来源：`Tool.to_openai_schema()` 从 `args_model`（Pydantic）生成，不手写第二份 JSON schema——手写就会出现「schema 和实际校验不一致」这类 bug。
`[PRODUCTION_NEXT]` 生产环境我会再加：工具注册表持久化 + 版本、按租户/部门可见性、危险动作标记（写操作必须审批）、以及 MCP 引入时把它作为**治理边界而不是便利层**（见 §10）。

#### My Project Evidence

- `app/agent/registry.py`、`app/agent/tools/__init__.py::DEFAULT_TOOL_NAMES`
- `app/agent/tools/base.py::Tool`（`name/description/args_model/permission/parameters/validate`）
- `tests/unit/test_permissions.py::TestDefaultRegistry`（4 工具、重名失败、未知失败、schema 生成、operation 白名单）
- `tests/integration/test_web_console_contract.py::test_tool_whitelist_is_the_four_shipped_tools`

#### Follow-up Questions

- 白名单是代码写死的，配置化/动态注册怎么做？安全上要注意什么？
- 工具多了以后 schema 会吃掉大量 context，怎么裁剪？
- 第三方工具（MCP server 给的）能不能进白名单？

#### Pitfalls

- 不要说「白名单是为了防止 SQL 注入」——SQL 注入是靠参数化查询防的，白名单防的是「能力面失控」。两者要分开说。
- 不要暗示运行时可以热加载任意工具；我不会允许一个不在代码/测试里的工具出现在 Agent 面前。

#### Interview Keywords

`capability whitelist` `schema single source` `permission on the tool` `fail-fast registration`

---

## Q5-05 ToolExecutor 具体做什么？

#### Short Answer

它是工具执行的唯一边界，固定四步：查白名单 → 查权限 → 校验参数 → 执行，然后把一切异常包成结构化失败，并顺手产出这一条调用的审计与指标。

#### Standard Answer

`[MY DESIGN]` `ToolExecutor.execute(call, actor=…)` 内部顺序是：
① `registry.get(name)`，未知工具 → `ToolResult(success=False, error_code="UNKNOWN_TOOL")`；
② 权限：`actor is None or not actor.is_authenticated` → `PERMISSION_DENIED`（**未认证即拒绝，fail-closed**）；`has_permission(actor.role, tool.permission)` 不通过 → `PERMISSION_DENIED`，并把 `permission_required`/`role` 放进 metadata；
③ `tool.validate(arguments)`（Pydantic）→ 失败 → `INVALID_ARGUMENTS`（带紧凑的字段级摘要）；
④ `await tool.execute(arguments)` → 任何 `Exception` 都被兜住 → `TOOL_ERROR`，错误文本带异常类型名但不带 traceback。
执行完在 `_observe()` 里统一：`metrics.observe_tool_call(tool, success, permission_denied)` + 一条结构化 `tool.call` 日志 + `audit.record_tool_call(...)`（`AuditStatus` 取 `success/denied/error`）。审计只记录白名单参数（`AUDITABLE_ARGUMENT_KEYS = operation/days/limit/material/area/status/mode`），**绝不记录 prompt 或结果正文**。
契约保证：**这个方法永不 raise**。这一点是设计上的关键——因为异常一旦逃出来，Agent loop 就得自己处理，权限/审计就会漏。
（诚实说明：`is_allowed()` 这个辅助方法在 `actor=None` 时返回 `True`，它只被测试用于「有 actor 时的角色判断」；真实执行路径 `_execute` 是 fail-closed 的。这是 §21 审查留下的可改进点之一。）

#### My Project Evidence

- `app/agent/executor.py`：`ERROR_UNKNOWN_TOOL/ERROR_TOOL_FAILED/ERROR_INVALID_ARGUMENTS`、`_audit_summary`、`_observe`
- `tests/unit/test_agent_permissions.py`：`test_denial_happens_before_any_data_access`、`test_without_an_actor_the_executor_denies_tools`、`test_actor_none_denies_knowledge_tool`、`test_denied_call_is_audited_and_counted`
- `tests/integration/test_rbac.py::test_agent_tool_denial_writes_a_denied_row`

#### Follow-up Questions

- 工具超时你怎么处理？现在有吗？
- 如果工具是写操作（比如发起一个审批），executor 需要多做哪些事？
- 权限判断为什么不在 registry.get 里做？

#### Pitfalls

- 不要说「executor 负责重试」。我没有实现重试或退避，这是缺口（§22）。
- 不要把「不 raise」说成「不会出错」——是错误被结构化了，不是消失了。

#### Interview Keywords

`permission → validate → run` `never raises` `audit + metrics` `fail-closed`

---

## Q5-06 为什么 Tool 还需要二次 RBAC？前端隐藏 / 路由检查不算吗？

#### Short Answer

因为 Agent loop 不经过路由。路由只保证「谁能调 `/api/agent/run`」，而一次 agent.run 里模型可能请求 4 个工具中的任何一个——那一步的权限只有在 executor 里查才算数。

#### Standard Answer

`[MY DESIGN]` 我把权限分成两个**不互相继承**的家族（写在 `app/auth/permissions.py` 的模块文档里）：路由权限（`chat:run`、`agent:run`、`audit:read`、`knowledge:ingest`、`users:manage`…，由 `require(...)` 在 FastAPI 依赖里执行）和工具权限（`tool:knowledge`、`tool:erp`、`tool:safety`，由 `ToolExecutor` 在执行前执行）。
`POST /api/agent/run` 只要求 `agent:run`，三个角色都有。所以 operator 有权「跑 Agent」，但**没有 `tool:erp`**。结果就是：HTTP 200、Agent 正常收尾、`tool_calls[].success=false`、`error_code="PERMISSION_DENIED"`，审计写一条 `tool.call=denied`，指标 `permission_denied_count +1`。这条行为在 `tests/integration/test_rbac.py::test_erp_tool_is_denied_for_operator` 里钉住，`test_denial_happens_before_any_data_access` 进一步断言**数据库根本没被碰**。
为什么不做成「403 直接失败」？因为越权在 Agent 场景里是**常态而不是事故**：模型可能猜错工具的适用对象。把常态做成 500/403 会让整个会话不可用，也会诱使前端去做「隐藏按钮就算安全」的假边界。受控拒绝 + 留痕 + 让用户换个问法，才是可运维的行为。
另外：前端隐藏按钮只是 UX。Web Console 切角色只是换 Authorization header，权威判断永远在后端——`GET /api/audit`、`GET /api/models` 对 operator 是真的 403。

#### My Project Evidence

- `app/auth/dependencies.py::require`（403 + 审计 `denied`；401 因无 user_id 不落库，只进日志/内存）
- `app/agent/executor.py`（第二次检查）
- `tests/integration/test_rbac.py`（32 个 case：missing token 全端点 401、operator 403/工具拒绝、manager 边界、admin 全通过、route denial 审计）
- `tests/integration/test_web_console_contract.py::test_denied_tool_is_a_labeled_controlled_failure`
- `DEMO_SCRIPT.md` Step 5（现场演示这一条对比）

#### Follow-up Questions

- 会不会出现「工具权限通过但数据权限不足」的情况？怎么防？
- 权限矩阵怎么测试到不会漏？
- 如果以后要做审批型写工具，权限模型怎么改？

#### Pitfalls

- 不要说「我们有纵深防御所以很安全」。只有一处会真授权：`has_permission` 这一个函数 + 角色矩阵；说清这点更可信。
- 不要把 `Permission` 字符串和 `tool` 名字混着说——`permission_for_tool()` 那张映射表和 `Tool.permission` 属性目前是两个地方各写一次（见 §22），被问到要承认。

#### Interview Keywords

`tool-level RBAC` `two permission families` `controlled denial` `no UI trust`

---

## Q5-07 request_id 怎么传播？

#### Short Answer

纯 ASGI 中间件生成或沿用 `req_<uuid4>`，同时写三处：响应头 `X-Request-ID`、`scope["state"]`、日志 ContextVar；HTTP 依赖把它读出来塞进 `Actor`，`Actor` 再随工具调用传进 executor 和 audit。

#### Standard Answer

`[MY DESIGN]` `RequestContextMiddleware.__call__`（非 http scope 直接放行）按优先级取 ID：请求头 `X-Request-ID`（非空且 ≤128 字符才采信）→ `scope["state"]` → 新生成。之后：把 `request_id` 写入 `scope["state"]["request_id"]`；包一层 `send`，在 `http.response.start` 时把它补进响应头（不覆盖已有）；整个下游调用包在 `request_id_scope(request_id)` 里（`contextvars`），所以那一条链上所有日志行都自动带 request_id；结束时统一记录耗时与状态并喂 `metrics.observe_request`。
进入业务层的路径是显式的：路由用 `Depends(request_id_of)` 取值，构造 `Actor.from_user(user, request_id)`，把 `actor` 传给 `AgentRuntime.run(...)`，executor 用它写 `record_tool_call`。`AgentRunResult.request_id` 也回带它。所以一次 agent.run 里 `http.request` / `agent.run` / N 条 `tool.call` 全都是同一个 ID。
我特意**没有**做隐式全局传递（比如把 request_id 塞进环境变量或模块级单例）：异步并发下 ContextVar 是安全边界，跨请求对象传递必须是显式参数。
`[PRODUCTION_NEXT]` 下一步是接 OpenTelemetry：把 `request_id` 对齐成 trace_id、把每一步 LLM/工具变成 span、以及把上游 `X-Request-ID` 的格式做校验与截断策略（现在是长度上限）。

#### My Project Evidence

- `app/observability/middleware.py`、`app/observability/logging.py`（`REQUEST_ID_HEADER`、`_request_id` ContextVar、`request_id_scope`、`JsonFormatter`）
- `app/api/agents.py`（`Actor.from_user` → `service.run(actor=…)` → 响应体 `request_id`）
- `tests/integration/test_platform.py::TestRequestId`（每个响应都带 / body 与 header 一致 / 沿用外部传入 ID / 一次 agent run 全链同一个 ID / 错误响应也带 ID）

#### Follow-up Questions

- 如果客户端伪造 X-Request-ID 会怎样？
- 队列/异步任务（脱离 HTTP 请求）怎么延续同一条链？
- 为什么不直接上 OpenTelemetry？

#### Pitfalls

- 不要说「我们用了 W3C traceparent」。我用的是 `X-Request-ID` 头，被追问就照实说。
- 不要忽略「401 不落库」这个细节：`audit_logs.user_id` 是 NOT NULL，匿名失败尝试只进日志与内存——这是我如实说明的取舍，不是遗漏。

#### Interview Keywords

`X-Request-ID` `ContextVar` `Actor` `correlation not causation`

---

## Q5-08 Audit 为什么不能只记录 HTTP 请求？

#### Short Answer

因为在 Agent 系统里，「一次 HTTP 请求」和「一次有业务含义的动作」不是一回事：一次 agent.run 里可能有 3 次模型调用、5 次工具执行、2 次越权拒绝。只记 HTTP，出事时你不知道它到底做了什么。

#### Standard Answer

`[MY DESIGN]` 我的审计表是**双形状同表**（`AuditAction`）：
**实际落库的 API 级事件**：`chat.complete`、`knowledge.ingest`、`knowledge.search`、`agent.run`（列：`endpoint/model_name/mode/status/latency_ms/input_summary`）。
`[MY DESIGN → 已知缺口]` `AuditAction` 里我还声明了 `knowledge.documents`、`audit.read`、`models.list` 三个动作名，但这三个端点**目前不写审计行**（`GET /api/knowledge/documents`、`GET /api/audit`、`GET /api/models` 只做了鉴权）。也就是说「看审计要不要留痕」这个问题，我现在的诚实答案是**没留痕**——这是 §22 明列的待补项，常量声明只是给它留了位置。
工具级事件：`tool.call` 一行一次调用（`tool_name` + `status=success|denied|error` + 只有 `operation/days/limit/…` 这类安全参数）。
两类事件靠 `request_id` 串成一条链，`GET /api/audit/{request_id}` 直接返回整链。
举三个只有细粒度审计才能回答的问题：① operator 的 ERP 越权尝试是什么时候、在哪个工具上被拒的？（`tool.call=denied` 那行，和同一请求里 `agent.run=denied/success` 的状态一起看）② 某次 ingest 是谁触发的、导了几篇文档几个 chunk、当时用的哪个模型？③ 一次回答的 5 条引用里有没有某条来自不该出现的文档？
还有一个必须说清的隐私约束：`AuditLog.record()` 里统一 `sanitize_summary`——denylist 把 `authorization/api_key/token/secret/password/prompt/messages/content/text/chunks` 这类 key 直接丢弃，嵌套结构只留长度，字符串截到 160 字符，最多 12 个 key；写库失败**只告警不抛出**（审计不能把主请求打挂），内存里 `deque(maxlen=AUDIT_MEMORY_MAX_RECORDS=1000)` 有界。
`[PRODUCTION_NEXT]` 生产化要加的是**不可篡改性**：append-only + 独立写库账号 + 定期哈希链/签名锚定 + 冷存储归档 + 保留策略，以及权限升级：`user_id` 要绑真实身份，401 这类匿名事件要能单独存一张表而不是只留日志。

#### My Project Evidence

- `app/observability/audit.py`：`AuditAction`、`AuditStatus`（`success/error/denied/unauthenticated/not_found/conflict`）、`DENYLIST_TERMS`、`sanitize_summary`、`record`、`record_tool_call`
- `app/api/audit.py`（分页 + `tool/action/status/request_id/user_id` 过滤 + 未知 request_id → 结构化 404）
- `tests/unit/test_audit.py`（`TestPrivacy::test_secrets_are_never_persisted`、`TestResilience::test_write_failure_never_raises`、`test_anonymous_events_stay_in_memory_only`）
- `tests/integration/test_platform.py::TestAuditApi`

#### Follow-up Questions

- 审计数据谁能看？看审计要不要留痕？（**当前没留痕** → 我会先补 `audit.read` 一行，因为「无痕翻看别人」是我自己这份清单上的第一条真实缺口）
- 如果审计写不进去，你是让请求失败还是让它通过？
- 合规要求保留 6 个月，你怎么做？

#### Pitfalls

- 不要说「审计 = 日志」。区别在 §15 里明确：审计是**面向质证的、结构化的、有身份的、不记 prompt 的**记录，日志是面向排障的、可以很啰嗦。
- 不要说「我的审计不可篡改」——它就是普通 SQLite 表，被问必须承认（§22）。
- 不要说「所有端点都有审计」。落库的是 4 类写/执行动作；三个只读端点（documents / audit / models）目前只有鉴权没有留痕，被问必须承认（§22）。

#### Interview Keywords

`one row per action` `request_id chain` `sanitization` `append-only next`

---

## Q5-09 Metrics 和 Audit 有什么区别？

#### Short Answer

Audit 回答「这一次发生了什么、谁做的」，是取证粒度；Metrics 回答「这段时间整体怎么样」，是运维粒度。前者必须可追溯、不落敏感内容；后者必须便宜、可丢弃重启。

#### Standard Answer

`[MY DESIGN]` 我具体做成两套东西：`AuditLog`（`app/observability/audit.py`）**持久化到 SQLite**，每事件一行、带 user/role/request_id/状态/延迟；`Metrics`（`app/observability/metrics.py`）是**进程内计数器 + 锁**，`GET /metrics` 输出 JSON 文档。
语义差别我这样表述：审计是**面向质证的**（谁、什么时候、试了什么、成功还是被拒），所以有 `denied`/`unauthenticated`/`not_found`/`conflict` 这些状态；指标是**面向决策的**（要不要告警、要不要扩容、哪个端点变慢、错误码分布、被拒次数是否突增），所以只有计数与均值/峰值。
两套系统在同一位置埋点，所以数字能对上：`RequestContextMiddleware` → `observe_request`；`ToolExecutor._observe` → `observe_tool_call` + `record_tool_call`；`AgentService.run` → `observe_agent_run(status)`；`AuditLog.record` 成功写库 → `observe_audit_write`。审计行数与 `audit_write_count` 一致，`permission_denied_count` 与 `tool.call=denied` 的行数一致。
取舍要说透：指标重启清零是**故意的**——它不该是真相来源，真相来源是审计。生产环境我会把指标换成 Prometheus（`Metrics.snapshot()` 已经是现成的采集面），但审计仍然必须是有身份、可追溯的记录。

#### My Project Evidence

- `app/observability/metrics.py`（15 个字段：request/success/error/avg_latency/max_latency/by_status_class/by_endpoint/error_by_code/tool_call/tool_error/permission_denied/agent_run/agent_runs_by_status/audit_write/uptime）
- `app/api/metrics.py`（公开：无业务数据、无身份；注释里写明了这一点）
- `tests/unit/test_metrics.py`、`tests/integration/test_platform.py::TestMetricsApi`（含 `test_metrics_is_json_not_prometheus_text`）

#### Follow-up Questions

- 为什么不直接上 Prometheus？
- 哪些指标值得告警？阈值怎么定？
- 高基数（per-user / per-model）指标怎么控制？

#### Pitfalls

- 不要说「两个都是可观测性所以差不多」。
- 不要把 `/metrics` 公开说成安全设计亮点而不加限定：我说的是「载荷只有计数器、无业务数据、无身份」，生产上仍会加网络隔离或鉴权。

#### Interview Keywords

`audit = forensics` `metrics = operations` `same instrumentation points` `restart-safe vs not`

---

## Q5-10 为什么用 SQLite？

#### Short Answer

因为它把「业务数据 + 审计 + 用户」三件事零运维地解决了，而且测试可以在 tmp 目录里为每个 case 建一个独立库——这是我这个项目最重要的约束之一。

#### Standard Answer

`[MY DESIGN]` 具体选择：`DATABASE_URL=sqlite:///./data/runtime/app.db`，SQLAlchemy 2 + 同步 engine + `session()` 上下文管理器（成功 commit、异常 rollback、一定 close）；`connect` 事件里 `_enable_foreign_keys`，因为 SQLite 默认不强制外键，而 `audit_logs.user_id → users.id` 需要是真的。`data/runtime/` 挂进 Docker 卷，所以重启数据在（我验证过审计行数、Chroma 文档数、旧 request_id 轨迹）。
我明确不要的东西：一个额外的数据库服务。SPEC 里就把 K8s/Kafka/Redis/微服务列为本期禁止扩张项；多加一个组件，我就要多回答一次「它挂了怎么办、谁备份、怎么扩」。
但 SQLite 的限制我很清楚：写路径单文件锁、并发写会 `database is locked`、多进程多副本共享麻烦、类型系统宽松、没有真正的角色级权限（所以审计表的不可篡改性在这个 Demo 里**没有**做到）。
`[PRODUCTION_NEXT]` 生产上第一步就是换 Postgres：`audit_logs` append-only + 独立写账号 + 分区/归档 + 真权限；业务侧数据我不打算自己搬——它属于 ERP，正确做法是只读账号/只读视图（见 §9）。

#### My Project Evidence

- `app/config.py::database_url`、`app/db/database.py`（`normalize_url` 把相对路径解析到仓库根、`_enable_foreign_keys`、`session`）
- `app/db/models.py`（9 张表 ORM 是唯一事实来源）、`data/synthetic/schema.sql`（参考 DDL）
- `tests/unit/test_database.py::TestSchemaConsistency`（ORM 与参考 DDL 的表和列必须一致）

#### Follow-up Questions

- 为什么不让 ORM 自动迁移（Alembic）？
- 并发写你现在会怎么坏？
- 迁移到 Postgres 时最容易踩的坑是什么？

#### Pitfalls

- 不要说「SQLite 不适合生产，但 demo 无所谓」——要给出它适合/不适合的具体维度（并发写、副本、权限、锁）。
- 不要假装迁移是零成本：SQL 方言、`LIMIT/OFFSET` 参数绑定、日期处理、连接池都要过一遍。

#### Interview Keywords

`zero-ops storage` `test isolation` `foreign keys on` `known ceiling`

---

## Q5-11 为什么用 Chroma？

#### Short Answer

因为我要的是「一个本地持久化集合 + 一次 embedding 相似度查询」这个最小能力，Chroma 能在同进程内给到，且能被 `VectorStore` 一层薄封装隔离掉。

#### Standard Answer

`[MY DESIGN]` `app/rag/store.py::VectorStore` 是全项目**唯一允许 import chromadb 的模块**（文件首行就这么写的），它包 `PersistentClient(path)` + `get_or_create_collection` + `add/query/count/delete`。检索逻辑在 `retriever.py`，分块在 `chunker.py`，所以换向量库只需要重写 `store.py` 这一个文件。
第二个关键决定：**不使用 Chroma 内置 embedding function**，向量一律由我的 `EmbeddingProvider` 显式传入。这样 embedding 的可替换性是平台层的性质，不是向量库的性质——也保证离线零下载。
我为什么没在 Demo 阶段直接上 pgvector 或 Qdrant：① 不引入额外服务（与 SQLite 同一理由）；② 面试要展示的点是检索管线（分块 → embedding → 融合打分 → citation → 回答策略），这些跟向量库品牌无关。
诚实的限制：Chroma 这里跑的是**单进程嵌入式**模式，多副本共享同一目录不是我验证过的能力（`data/runtime/chroma` 里能看到多个 collection UUID 目录）；大向量维度（1024）+ hash-ngram mock 只是「足够跑通管线」，不是语义检索质量的保证。
`[PRODUCTION_NEXT]` 生产上我要的是**metadata 过滤 + 权限 + 版本**：文档 ACL 落到 metadata 或关系库；混合检索（BM25/sparse + dense）+ rerank；索引与文档版本对齐，可回滚；以及和 Postgres 同库（pgvector）还是独立向量服务的取舍，判据是数据量、QPS 和团队运维半径。

#### My Project Evidence

- `app/rag/store.py`（`UPSERT_BATCH=256`、`PersistentClient`、只此一处依赖 chromadb）
- `app/rag/retriever.py`（融合打分：`VECTOR_WEIGHT=0.5 / BODY_WEIGHT=0.25 / HEADER_WEIGHT=0.25`，`OVER_FETCH=4`，`MAX_CANDIDATES=200`，`min_score=0.10` 过滤）
- `app/embeddings/base.py` + `app/embeddings/mock.py` + `app/embeddings/openai_compatible.py`
- `tests/unit/test_retriever.py`、`tests/unit/test_embeddings.py`

#### Follow-up Questions

- 为什么检索质量现在够用？你打算怎么量化？
- pgvector 和独立向量库怎么选？
- 文档更新时索引和 chunk 的一致性怎么保证？

#### Pitfalls

- 不要说「Chroma 性能差/好用」这类没有测量过的判断。
- 不要把 hybrid 检索说成「语义检索」——我的 lexical 部分就是 CJK bigram 重合率，被追问要如实说明。

#### Interview Keywords

`single integration point` `explicit embeddings` `metadata for citations` `pgvector next`

---

## Q5-12 为什么没有 Redis？

#### Short Answer

因为在这个范围里 Redis 能提供的三件事（缓存、会话、队列）我一件都还没有真实的性能压力需求，而引入它的运维与一致性成本是立刻发生的。

#### Standard Answer

`[MY DESIGN]` 我的 loop 是无状态的：一次请求一个 `AgentState`，不共享、不驻留，所以我不需要外部会话存储；模型输出目前不做缓存（要缓存必须先解决权限与新鲜度：同一段文本对 manager 可给、对 operator 未必可给，RAG 结果还依赖当时知识库状态）；没有异步任务，所以不需要 broker。SPEC 里也把 Redis 列为本期禁止扩张项。
我什么时候会引入它，判据写清楚：
① **会话/多轮上下文持久化**：当我要支持长会话、跨进程恢复或断点续跑时，用 Redis 或 Postgres 存 run 状态（取决于要不要事务与审计）；
② **限流与配额**：当平台按部门/用户控成本时，滑窗计数放 Redis（`[PRODUCTION_NEXT]` 这也是 JD 里「结合成本优化模型选型」的基础设施）；
③ **异步/长任务**：批量 ingest、评测跑批、报表生成放任务队列；
④ **响应缓存**：只在能按 `(principal, permission set, index version)` 三元组做 key 的前提下才做，否则就是权限漏洞。

#### Follow-up Questions

- RAG 结果缓存你担心什么？
- 多 worker 部署时你现在有什么会坏？

#### Pitfalls

- 不要说「Redis 没必要」。要说「现在没有对应的压力，并且有明确的引入判据」。
- 必须主动承认：`uvicorn` 多 worker 时，我的进程内 `Metrics` 计数、`AuditLog` 内存副本、`MockProvider` 的脚本状态都是每进程各一份，这会造成指标分裂与状态不一致——这正是需要共享基础设施的第一个信号。

#### Interview Keywords

`no premature infra` `shared vs process-local` `cache invalidation = permission problem`

---

## Q5-13 为什么没有 Kubernetes？

#### Short Answer

5 天里我要验证的是平台层逻辑，不是编排。Docker Compose 已经覆盖了我想演示的运维事实：可构建、可健康检查、可反代、卷持久、重启不丢数据。

#### Standard Answer

`[MY DESIGN]` 现在是两个容器：API（`docker/api.Dockerfile`：`python:3.11-slim` + `uv sync --frozen --no-dev --no-install-project`，healthcheck 用 stdlib urllib 打 `/health`，不额外装 curl）和 Web（`web/Dockerfile`：`node:22-alpine` 构建 → `nginx:1.27-alpine` 托管，`:3000→80`）。
`depends_on: api: condition: service_healthy` 解决启动顺序 502；nginx 反代用变量 + Docker 内嵌 resolver（`resolver 127.0.0.11 valid=10s` + `set $api_upstream`），这样 API 重启时 nginx 不会因为启动期解析失败而拒绝启动——这是我真实遇到的坑，也是我愿意讲的运维细节。`./data/runtime` 挂卷，`documents` 与 `synthetic` 只读挂载。
为什么不是 K8s：单节点 + 两服务 + 一份持久数据，K8s 带来的收益（自愈、弹性、灰度、多节点调度）在这里演示不出来，成本（网络策略、存储类、CI、镜像仓库、rbac、可观测接入）全是真的。
`[PRODUCTION_NEXT]` 什么时候值得上：多副本无状态服务要弹性伸缩、GPU 推理服务要调度和共享、需要滚动发布与回滚策略、需要跨环境（办公网/基地/云上）一致性交付。上之前我会先把两件事做完：应用真正无状态（把指标与会话挪到共享存储）、以及镜像与配置分层（secrets 进 Vault/K8s Secret，绝不进镜像与 Git）。
`[INFERENCE]` 对恒光这种场景，我的判断是「私有化 + 少量节点 + 可人工运维」优先于「云原生编排成熟度」，所以我会先做单节点可回滚 + 备份演练，再谈 K8s。这是我根据公开资料和 JD 做的技术推演，不是对公司现状的了解。

#### My Project Evidence

- `docker-compose.yml`、`docker/api.Dockerfile`、`web/Dockerfile`、`web/nginx.conf`
- `README.md` §Docker Compose 最终验证（清单：config 解析、两服务 build+start、反代 200、stop/up 后 SQLite/Chroma 数据与旧 request_id 仍在、运行中调用 agent/metrics/audit/ingest 正常）

#### Follow-up Questions

- 两节点之间怎么共享 Chroma 和 SQLite？你现在做得到吗？
- 如果只能有一台 GPU 服务器，你会怎么部署这个平台？
- 你怎么做回滚？

#### Pitfalls

- 不要说「K8s 太复杂所以不用」。理由是收益/成本不匹配 + 我没有需要它的负载。
- 不要宣称「我已经生产部署过」——我只做了 Compose 级别的验证。

#### Interview Keywords

`compose is enough for the claim` `resolver + healthcheck` `statelessness before scale-out`

---

## Q5-14 为什么不是微服务？

#### Short Answer

因为我的分层已经是模块化的，模块边界（api / gateway / embeddings / rag / agent / db / auth / observability / services）就是未来的服务边界；现在把它们拆成网络调用只会引入分布式失败模式，而不带来任何独立伸缩需求。

#### Standard Answer

`[MY DESIGN]` 我的分层是有实际约束的，不是目录好看：模型出口只有一个（`ModelGateway`）、工具入口只有一个（`ToolRegistry`）、工具执行边界只有一个（`ToolExecutor`）、向量库依赖只有一个模块（`rag/store.py`）、身份与权限只在一处（`auth/`）。每个依赖方向都朝内，`app/api/router.py` 的注释里我还专门写了「不要在包 `__init__` 里急切 import 路由，否则 agent 层依赖 errors、路由依赖 agent 层会成环」——这是我真的被循环导入咬过之后留下的注释。
拆微服务的前提是**独立的伸缩或独立的所有权**。我现在两个都没有：负载是一个进程能扛的负载，所有权是一个人。
`[PRODUCTION_NEXT]` 我会优先在三个点考虑拆：① 模型推理服务（GPU 伸缩曲线完全不同，可能干脆是 vLLM/Ollama）；② 索引/ingest 与在线检索（批量重建不应该挤占在线延迟）；③ 审计/日志管道（写放大会独立增长）。拆的顺序是先抽 **进程内接口**、确认边界稳定，再决定要不要跨网络。

#### My Project Evidence

- 模块清单：`app/{api,gateway,embeddings,rag,agent,db,auth,observability,services}`（约 6.8k 行 Python）
- 依赖收口证明：`app/gateway/base.py` 的 Protocol、`app/agent/registry.py`、`app/agent/tools/__init__.py`、`app/rag/store.py`
- `app/api/router.py`（避免 router 成环的注释）

#### Follow-up Questions

- 那什么时候你会把它拆成两个服务？
- 单体部署的一个进程崩了会丢什么？（指标 + 内存审计副本，DB 与 Chroma 不丢）

#### Pitfalls

- 不要说「微服务是过时的」。说「在这个负载和这个所有权结构下收益不成立」。
- 不要说「我的代码是单体的所以不能水平扩」——Web 层可以随意扩，API 层可以无状态多副本，但要先解决 §5-12 里那些进程内状态。

#### Interview Keywords

`module boundaries = future service boundaries` `scale or ownership` `in-process first`
# 6 · Model Gateway

## Q6-01 什么是 Model Gateway？

#### Short Answer

一个进程内的统一模型访问层：把「用哪个模型、怎么调、失败怎么办、降级要不要让人看见」这四件事收进一个地方，业务代码只看到一个 `chat()`。

#### Standard Answer

`[MY DESIGN]` 我的实现是 `app/gateway/router.py::ModelGateway`，对外主方法只有一个：
`async chat(messages, *, model=None, provider=None, temperature=0.2, response_format=None, tools=None) -> ModelResponse`。
它做四件事：
① **构造期注册**：`_init_providers()` 里 mock 恒在；真实 provider 必须同时有 `llm_base_url` 与 `llm_api_key` 才注册；
② **运行期选取**：`get_provider(name)`，取不到退回 mock（保证永远有出口）；
③ **归一化输出**：所有 provider 都返回同一个 `ModelResponse(content, model, provider, usage, latency_ms, tool_calls, degraded)`；
④ **失败决策**：按 `LLM_FALLBACK` 决定是否降级到 mock 并打 `degraded=True`；否则抛 `RuntimeError`，由 API 层转成 502 `PROVIDER_ERROR`。
另外 `BaseProvider.chat` 做入参校验（空 messages、temperature ∉ [0,2] 直接 `ValueError`），保证参数错误不会被带到网络上。
定位一句话：**它是模型侧的能力接口，不是一个模型服务**。生产版本会长成独立服务，但抽象形状不变。

#### My Project Evidence

- `app/gateway/base.py`：`ModelProvider`（`@runtime_checkable` Protocol）、`BaseProvider`、`ModelResponse`、`ToolCall`
- `app/gateway/router.py`：`_init_providers` / `get_provider` / `chat` / `list_models`
- `app/api/chat.py`：provider 失败 → `ProviderError` 502 + 审计 `error`
- `tests/unit/test_gateway.py`（19 个测试）

#### Follow-up Questions

- 网关会不会长成上帝类？你打算怎么切？
- 它和 API 网关（Kong/APISIX）什么关系？
- prompt 模板归不归网关管？

#### Pitfalls

- 不要说「就是个 wrapper」。它有四类决策职责（注册/路由/降级/目录），这才是网关。
- 不要说它已经做了限流、缓存、计费、重试——都没有（见 §22）。

#### Interview Keywords

`single choke point` `ModelResponse` `explicit fallback` `provider registry`

---

## Q6-02 为什么需要 Provider abstraction？

#### Short Answer

因为厂商 API 的差异不该渗进业务代码；而且我需要一个零网络、零 Key 的实现来跑完 423 个测试。

#### Standard Answer

抽象的具体形状是一个 Protocol：`async chat(messages, *, model, temperature, response_format, tools) -> ModelResponse`。`tests/unit/test_gateway.py::test_mock_provider_implements_protocol` 用 `isinstance` 把「实现必须满足协议」钉成测试。
两个实现：
- `MockProvider`：确定性响应（同样输入 → 同样输出），三种行为（plain chat / agent tool-calling / 脚本化队列），是全部测试与离线演示的基础；
- `OpenAICompatibleProvider`：`httpx.AsyncClient` 打 `/chat/completions`，`Authorization: Bearer <key>`；`tool_calls` 经 `parse_tool_calls()` 归一化——容忍缺 id（补 `call_N`）、`arguments` 是坏 JSON（变 `{}`），因为这些畸形输入交给 executor 会变成**受控失败**，不该在这里 500。
一个便宜的技巧：`provider_name` 从 `base_url` 推断（deepseek / qwen·dashscope / ollama / openai-compatible），所以我不需要为每家写一个类，`/api/models` 却能显示真实供应商名字。
`[PRODUCTION_NEXT]` 真平台上如果已经有一体化模型网关（`[FACT]` JD 第 2 条列了 one-api/new-api 这一类），我会把 `OpenAICompatibleProvider` 指向它——**换实现不换接口**，这正是抽象存在的意义。

#### My Project Evidence

- `app/gateway/openai_compatible.py`（`parse_tool_calls`、`provider_name` 推断、`timeout=60.0`、`stream=False`、`raise_for_status()`）
- `app/gateway/mock.py`（plain / agent / scripted 三态 + 抽取式带引用回答）
- `app/embeddings/openai_compatible.py`（同一形状用于 embedding）
- `README.md` §真实 LLM Provider 配置

#### Follow-up Questions

- 只支持 OpenAI 兼容协议，遇到私有协议怎么办？（写 adapter；不承诺「零改动接一切」）
- provider 的特有能力（thinking、cache_control）怎么表达？（扩展 kwargs 而不是破坏协议）
- 你怎么测「真实 provider 挂了」？（注入一个必然抛错的 fake provider——我正是这么测 fallback 的）

#### Pitfalls

- 不要说「抽象了就能换任何模型」。准确说法：**只要新 provider 说 OpenAI 兼容协议，就只改配置**。
- 不要否认 OpenAI 兼容 ≠ 完全一致：`response_format`、usage 字段、tool-call 细节各家有差，我目前只覆盖 chat + tools 主干。

#### Interview Keywords

`Protocol dependency` `adapter not per-vendor class` `tolerant tool-call parsing` `deterministic mock`

---

## Q6-03 如何切换 DeepSeek / Qwen / Ollama？

#### Short Answer

改环境变量：provider 名 + base_url + model（+ 需要 key 的给 key）。代码零改动，重启进程即可。

#### Standard Answer

```bash
LLM_PROVIDER=mock                      # 默认：零 Key、零外网

    # DeepSeek：
LLM_PROVIDER=deepseek LLM_BASE_URL=https://api.deepseek.com/v1 LLM_API_KEY=... LLM_MODEL=deepseek-chat
    # Qwen（DashScope 兼容模式）：
LLM_PROVIDER=qwen     LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 LLM_API_KEY=... LLM_MODEL=qwen-plus
    # Ollama（本机私有推理）：
LLM_PROVIDER=ollama   LLM_BASE_URL=http://127.0.0.1:11434/v1 LLM_MODEL=qwen2.5:14b LLM_API_KEY=ollama
    当前实现要求 base_url 与 api_key 都非空才注册 provider，
    本地端点不校验 key 时给一个占位值即可（§22）。

    embedding 独立配置，可以保持 mock 而 chat 用真实模型
EMBEDDING_PROVIDER=mock | openai-compatible（+ EMBEDDING_BASE_URL/API_KEY/MODEL）
```
一个我该主动说的机制：`get_settings()` 是 late-bound（请求路径每次读），但 **provider 注册发生在 `ModelGateway` 构造期**，所以「换 provider」实际是进程启动时决定的——我不会假装运行期热切换已实现。
还有一个刻意的门槛：`_init_providers()` 需要 `llm_base_url` **和** `llm_api_key` 同时非空。所以「配了个半拉子」的后果是明确的：注册表里只有 mock，`/api/models` 也看不到那个假 provider，不会出现「界面显示有 DeepSeek，实际全走 mock」。
我当前实际在跑的组合：`LLM_PROVIDER=modelscope` + ModelScope 端点（`https://api-inference.modelscope.cn/v1`）+ `Qwen/Qwen3.8-Flash-Next`（支持原生 tool calling），`/api/chat` 与 `/api/agent/run` 都走通；回答由真实模型生成、`provider != mock`，而 **citation 与审计链路完全没变**（Docker 默认 embedding 仍是 mock）。更早一轮（Day 5）跑通的是 `LLM_PROVIDER=openai-compatible` + 同一端点 + `deepseek-ai/DeepSeek-V4-Flash-0731`——两种写法都成立，因为 `LLM_PROVIDER` 只是网关的注册键，`/api/models` 的 default 判定同时认注册键和从 `base_url` 推断出的显示名。

#### My Project Evidence

- `app/config.py`（`LLM_*` / `EMBEDDING_*` 全部 env 驱动，`_env_bool`/`_env_int` 带默认）
- `app/gateway/router.py::_init_providers`（双条件门槛）
- `.env.example`（每一项都有注释）
- `README.md` §真实 LLM Provider 配置（冒烟记录）+ §已知限制（embedding 冒烟仍走 mock）

#### Follow-up Questions

- 运行期热切换怎么做才安全？（不可变 Settings 快照 + 原子替换 + 在途请求不混用）
- 多 provider 同时在线、按任务路由，你会怎么改？（网关内加一层 routing policy + 每任务的成功率/成本统计）
- key 怎么保证不进 Git / 不进日志 / 不进审计？（`.env` gitignore + 审计 denylist + `/api/models` 只报可用性不报凭据——这三处我都有）

#### Pitfalls

- 不要说「任何 OpenAI 兼容端点都能跑」。我只对做过冒烟的那一个端点做保证。
- 不要说「支持热切换」。现在是启动期决定。

#### Interview Keywords

`env-driven` `registration gate` `smoke-tested endpoint` `no runtime hot-swap yet`

---

## Q6-04 fallback 怎么设计？

#### Short Answer

显式开关 + 显式标记 + 只在真 provider 失败时生效 + 绝不对 mock 再降级；默认关闭，宁可 502 也不要静默换模型。

#### Standard Answer

`[MY DESIGN]` 逻辑在 `ModelGateway.chat()` 的 except 分支：
```text
if settings.llm_fallback and prov is not self._providers.get("mock"):
    response = await mock_prov.chat(...)
    return ModelResponse(..., degraded=True)     # 关键：重新构造并打标
raise RuntimeError(f"Model provider error: {e}") from e
```
四个设计点：
① **默认关闭**（`LLM_FALLBACK` 默认 false）：真 provider 挂了 → `RuntimeError` → API 层 `ProviderError` → **502 + 统一错误信封 + 审计 `chat.complete=error`**。让不可用性可见。
② **不循环降级**：mock 失败不再降级，避免死循环与假成功。
③ **降级可观测**：`degraded=True` 是响应契约的一部分，同时 `logging.warning("provider fallback triggered: %s -> mock")`。
④ **降级不换协议**：因为所有 provider 返回同一个 `ModelResponse`，Agent loop 与 RAG pipeline 完全不需要知道发生过降级——这是抽象层最实际的回报。
`[PRODUCTION_NEXT]` 我会把它从「全局布尔」变成**有类型的路由策略**：按任务分级（分类/抽取可降级到小模型；写审批意见不允许降级）、按预算（成本超阈值才降级并明确告知用户）、并在响应与审计里同时记录 `requested_model` / `actual_model` / `reason`，而不是只留一个布尔位。

#### My Project Evidence

- `app/gateway/router.py::chat`、`app/config.py::llm_fallback`
- `app/gateway/base.py::ModelResponse.degraded`
- `tests/unit/test_gateway.py`：`test_fallback_disabled_raises_error`、`test_fallback_enabled_returns_degraded`、`test_fallback_disabled_no_mock_circuit`
- `git show 460a6ee`（Fix #2 的 diff 与动机）

#### Follow-up Questions

- 什么条件下你允许自动降级？给判据。（任务不涉及事实生成 + 用户界面明确显示备用模型 + 降级计入指标）
- 降级时要不要通知用户？（企业内部平台：要。信任一旦因「假装正常的错答案」失去就很难回来）
- 你怎么防止降级被滥用成「反正有 mock」？（默认关 + 告警 + 把降级次数做成 SLO 指标）

#### Pitfalls

- 不要说「fallback 提升可用性」。它提升的是**不崩**，代价是**答案质量可能下降**，这个代价必须一起说。
- 不要说「默认开更稳」。静默降级正是我 code review 判定为缺陷的东西（§21 Fix #2）。

#### Interview Keywords

`opt-in degradation` `degraded=true on the contract` `fail visible by default` `no mock-of-mock`

---

## Q6-05 为什么 fallback 默认关闭？

#### Short Answer

因为「看起来成功的错误答案」在企业里比「明确的失败」更贵。默认关闭让不可用性可见，可见才能运维，也才可能追责。

#### Standard Answer

三条理由：
① **正确性优先**：这个平台给出的是**带引用**的答案，用户会以为背后真有模型在读资料。如果 provider 挂了而 mock 静默接管，输出仍然是「格式正确、内容无意义」的东西——这比 502 危险得多。
② **审计一致性**：审计里记 `model_name`。静默降级会让「谁实际生成了这条答案」变成假事实；而 model_name 是这件事唯一的记录位。`degraded` 位之所以有意义，前提就是降级必须显式。
③ **测试确定性**：如果降级默认开着，provider 故障会被 mock 吸收，我的集成测试就永远测不到 502 分支。现在两条路径各自被测试钉死（`tests/unit/test_gateway.py` 三条 fallback 用例）。
我也会正面回答「那可用性怎么办」：**降级不是可用性的唯一手段**。多 provider、超时预算、重试与熔断、请求排队才是；降级只是「让功能继续有输出」，不等于「让服务继续正确」。这两句话我面试时想明确区分。

#### My Project Evidence

- `app/config.py`（`_env_bool("LLM_FALLBACK", False)`）+ `.env.example` 显式写 `LLM_FALLBACK=false`
- `git show 460a6ee`（Fix #2 说明：silent model fallback → config gate + degraded flag）
- `app/observability/metrics.py`（`error_by_code.PROVIDER_ERROR` 让 502 可数）

#### Follow-up Questions

- 如果老板说「就是不能白屏，必须给个答案」，你怎么设计？（给答案 + 显式标「备用模型生成，未经知识库核对」+ 引导人工复核；不是偷偷给）
- 你怎么用指标证明静默降级有代价？（比较 `degraded` 样本与正常样本的引用一致率/点踩率）

#### Pitfalls

- 不要说「因为 SPEC 让默认关闭」——要给判断标准。
- 不要否认业务方的可用性诉求是真实的：承认它，然后把方案分层。

#### Interview Keywords

`fail visible` `silent degradation is a defect` `policy beats boolean`

---

## Q6-06 `degraded=true` 是干什么的？

#### Short Answer

它把「这条回答是降级产物」变成响应契约上的字段，让前端、审计和调用方都能分支处理，而不是只剩日志里一句 warning。

#### Standard Answer

`degraded` 是 `ModelResponse` 的布尔字段，默认 `False`。当网关因为真 provider 失败且 `LLM_FALLBACK` 打开而改用 mock 时，它**重新构造**一个 `ModelResponse(..., degraded=True)`（而不是复用 mock 的返回值，因为 mock 自己的 `degraded` 是 False）。
为什么要有它：① 前端可以显示「本次由备用模型生成」；② 评测与统计可以按 `degraded` 分桶，不把降级样本混进真实质量样本；③ 合规场景里「这条答案实际由谁产生」必须无歧义。
**现状限制我如实说**：在这个 Demo 里 `degraded` 还没穿透到 `/api/agent/run` 的响应体与审计行——它存在于网关返回值这一层，`AgentRunResult` 只有 `model`/`provider` 字段。这是我列在待办里的项，不是已完成的链路。

#### My Project Evidence

- `app/gateway/base.py::ModelResponse`（`degraded: bool = False`）
- `app/gateway/router.py::chat`（构造 `degraded=True`）
- `tests/unit/test_gateway.py::test_fallback_enabled_returns_degraded`
- 缺口对照：`app/agent/models.py::AgentRunResult`（无 degraded 字段）→ §22

#### Follow-up Questions

- 你会把 degraded 放进审计还是只放响应？（都要；审计记 `actual_model + degraded`，响应里给用户看）
- 降级时 `model` 字段应该报请求模型还是实际生成者？（报实际生成者，另加 `requested_model` + `reason`——报错误的那个是最危险的选择）

#### Pitfalls

- 不要说「前端已经有降级横幅」——UI 没做，只有字段。
- 不要说「degraded 已写进审计」。

#### Interview Keywords

`contract-level honesty` `not just a log line` `still incomplete`

---

## Q6-07 如果真实 provider 挂了怎么办？

#### Short Answer

分三层说清：平台现在确定的行为（502 + 审计 + 指标）→ 我第一步补什么（超时预算、熔断、备用 provider）→ 一条平台不变量（模型不可用时，鉴权与审计照样工作）。

#### Standard Answer

**当前 Demo 的确定行为**（可以指着代码与测试说）：
`/api/chat`：`gateway.chat` 抛错 → 写一条 `chat.complete=error` 审计（只含 `chars`、`error_type`，**不含 prompt 文本**）→ 抛 `ProviderError` → HTTP **502** + 统一信封 `{detail, request_id, error:{code:"PROVIDER_ERROR"}}` + `X-Request-ID`；指标 `error_count+1`、`error_by_code.PROVIDER_ERROR+1`、端点延迟计数更新。
`/api/agent/run`：路由层最后一张网 `except Exception` → 审计 `agent.run=error`（含 `INTERNAL_ERROR`）→ 结构化 500，响应里不含 traceback；`PlatformError` 直接透传，所以权限类失败仍按 401/403 表达。
**下一步（按性价比）**：① 总超时预算（现在只有 provider 的 `timeout=60.0`，没有「整次请求的墙钟预算」，重试会把它放大）；② 熔断 + 备用 provider（同协议直接注册第二个，路由按可用性选）；③ 关键路径分级：知识问答可以排队/降级，但**鉴权与审计必须优先保住**——模型挂了平台仍要能记录「谁试过、什么时候、失败了」。
**排障动作**：拿 `request_id` 查 `/api/audit/{request_id}` 确认失败发生在网关还是工具 → 看 `/metrics` 的 `error_by_code` 与 `requests_by_endpoint` 判断是单端点还是全局 → 容器侧看 healthcheck 与 JSON 日志。

#### My Project Evidence

- `app/api/chat.py`（provider 失败 → 审计 + 502）、`app/api/agents.py`（兜底 except → 审计 + 结构化错误）
- `app/api/errors.py`（`ProviderError`=502 / `ERROR_PROVIDER`、`_CODE_BY_STATUS`）
- `app/gateway/openai_compatible.py`（`timeout=60.0` + `raise_for_status()`）
- `tests/integration/test_chat.py`（19 个测试，含 provider 失败路径与审计）

#### Follow-up Questions

- provider 不挂但很慢（60s 不返回）怎么办？（现在的表现是 httpx 超时 → 502；生产要更短预算 + 可取消）
- 你怎么在不影响用户的前提下验证新 provider？（影子流量：同一请求发给新旧两个 provider，只把旧的返回给用户，比较质量与延迟）
- 网关挂了是不是整个平台挂了？（现在是同进程，所以是。这也是它「应该先做成一层、以后可拆成服务」的理由）

#### Pitfalls

- 不要说「会自动切备用模型」——默认不切，是刻意选择。
- 不要说「绝不会 500」。provider 异常在 chat 是 502，在 agent 兜底路径可能是 500 `INTERNAL_ERROR`（带审计、无 traceback）。说清细节比说漂亮话可信。

#### Interview Keywords

`controlled 502` `audit survives model outage` `timeout budget + breaker next`

---

## Q6-08 怎么做模型评测？

#### Short Answer

先定义任务与判据，再建固定评测集；指标是任务成功率、引用/忠实度、幻觉率、拒答准确率、P95 延迟和单次成本；同一套题跑多个 provider，「切换模型」才有依据。

#### Standard Answer

我会分四层（**以下全是 `[PRODUCTION_NEXT]`，我明确说明这是我的方法而不是我的成绩**）：
① **任务定义**：企业内部 AI 的任务不是「回答得好」，是「在给定知识源下回答可对、并可追责」。所以按能力拆：事实问答（RAG）、结构化数据解释（ERP/Safety 工具）、**路由正确性**（该不该调工具、调哪个）、**拒答正确性**（无依据时必须拒）。
② **评测集**：每类 30–100 条，含输入、期望要点、必须出现的引用、**禁止出现的内容**（如编造的数字/产能）。版本化在 Git 里，**与知识库快照一起锁版**——语料一变，分数就没有可比性，这是最容易被忽略的一致性陷阱。
③ **判分**：能用规则就用规则（数字对不对、引用 `document_id` 对不对、是否出现「没有足够信息」）；必须语义判断才用 LLM-as-judge，且 judge 固定模型 + 固定 prompt + 人工抽检，否则只是把不稳定往上搬了一层。
④ **对比与回归**：同一条评测集跑 N 个 provider（这正是网关抽象的用途），产出 `模型 × 指标` 矩阵 + 成本（`usage` 已从 provider 透传，只是还没进指标）+ P50/P95；上线前离线回归，上线后小流量影子对比；一次线上错误沉淀成一条永久回归样本。
**现状（诚实）**：`[MY DESIGN]` 我有的是**确定性回归基础**——mock provider 让「同一输入同一输出」成立，423 个测试覆盖检索、引用、拒答、工具选择、权限拒绝的断言。**我没有**跨模型准确率/幻觉率评测集。我不会把「测试全过」说成「效果好」。

#### My Project Evidence

- 已有：`app/gateway/mock.py`（脚本化 + 确定性）、`tests/unit/test_pipeline.py`、`test_retriever.py`、`tests/integration/test_agent.py`
- 已有数据面：`ModelResponse.usage` / `latency_ms`（成本与延迟的原始输入）
- 缺口：无评测集 / 无 judge / 无 `模型×指标` 对比 → §22

#### Follow-up Questions

- 只有 50 条样本你信吗？（信趋势不信绝对值；先做能自动化判分的规则子集，比做 500 条主观标注更值）
- 检索变好了但答案没变好，一般什么原因？（排序对了但上下文里塞了噪声；或 chunk 边界把关键句切坏——这正是 chunker 与 top_k 要一起调的原因）
- 业务方说「这答案不对」，你怎么变成工程资产？（复现 → 归因到检索/生成/口径 → 落成一条回归样本）

#### Pitfalls

- 不要报任何编造的百分比或排名。
- 不要把「加测试」当「做评测」：测试保证行为不漂移，评测保证质量。这是我刻意区分的两件事。

#### Interview Keywords

`rule-first scoring` `eval set versioned with corpus snapshot` `refusal tested both ways` `cost per task`

---

## Q6-09 企业模型选择应该看哪些指标？

#### Short Answer

先看能不能出域（合规/私有化），再看我自己的评测集上的质量、工具调用可靠性与引用能力，然后才是延迟与成本；最后一条硬指标是「它能不能被替换掉」。

#### Standard Answer

| 维度 | 我看什么 | 排序理由 |
|---|---|---|
| 数据边界 | 是否必须私有化；云端 API 允许传什么 | `[FACT]` JD 第 1 条明写「私有化 AI 平台」；`[INFERENCE]` 化工企业的制度/工艺/安全数据大概率不能出域 |
| 任务质量 | **在我自己的评测集上**的表现 | 榜单和我的场景无关 |
| 工具调用可靠性 | 是否稳定产出合法 function call、参数是否可被校验 | 我的 Agent 全靠这条；参数幻觉会被 Pydantic 拦成 `INVALID_ARGUMENTS`，但拦得多也说明不可用 |
| 上下文与引用能力 | 有效窗口、长文衰减、是否忠实带引用 | RAG 质量上限 |
| 中文与领域适配 | 中文语料、化工术语、单位与数字表述 | 我的语料全中文 |
| 延迟 | P50 / **P95** | 内部平台体感差在尾部，均值会骗人 |
| 成本 | 单次任务成本 + 峰值并发成本 | `[FACT]` JD 第 5 条「结合成本和效果」 |
| 部署运维 | 私有推理栈（vLLM/Ollama）、显存、并发吞吐、量化损失 | `[FACT]` 这岗位招 1 人 → 运维半径就是能力边界 |
| **可替换性** | 是否 OpenAI 兼容、有无厂商锁定 | 平台层必须允许我明年换掉它 |

**我不会做的事**：为了「用更大的模型」把所有请求都塞给旗舰模型。`[PRODUCTION_NEXT]` 平台应该按任务路由：抽取/分类/格式化走便宜模型，多步分析与成文走强模型，并且路由决策落在网关、审计与成本统计三处一致。

#### My Project Evidence

- `[MY DESIGN]` OpenAI 兼容抽象 = 可替换性的落地手段（`app/gateway/openai_compatible.py`）
- `[MY DESIGN]` 延迟与用量数据面已存在（`ModelResponse.latency_ms` / `usage`；`metrics.requests_by_endpoint`）
- 一次真实 provider 冒烟（`README.md` §真实 LLM Provider 配置）

#### Follow-up Questions

- 私有化小模型质量不如云端，你怎么跟业务方谈？（用评测集 + 明确「哪些任务私有模型已达标、哪些需要人审」，而不是二选一）
- 什么时候考虑微调而不是换模型？（见 Q7-11）
- 给你两周做一次最小选型实验，你怎么设计？（30–50 条自有题 + 2–3 个候选 + 规则判分 + P95 + 单问成本 → 一页对比表）

#### Pitfalls

- 不要背榜单（变化快、我无法验证、也容易被追问细节问倒）。
- 不要说「开源一定够用」或「必须上最强的」——给判据。

#### Interview Keywords

`data boundary first` `eval on my own set` `tool-call reliability` `P95 not mean` `substitutability`

---

# 7 · RAG

## Q7-01 RAG 是什么？

#### Short Answer

检索增强生成：先从外部知识里检索相关片段，把片段和出处一起放进 prompt，让模型「基于材料回答」而不是「凭记忆回答」；检索不到就明确说没有依据。

#### Standard Answer

它解决的是模型的一类固有缺陷：**不知道你的私有知识，而且不知道自己不知道**。
我的管线（`app/rag/`）：`ingest.py` + `extractor.py`（Markdown/TXT/PDF → 文本 + front matter）→ `chunker.py`（heading 感知分块）→ `app/embeddings/`（向量）→ `store.py`（Chroma 持久集合）→ `retriever.py`（融合打分 top-k + citation）→ `prompt.py`（回答策略 + 编号上下文块）→ `pipeline.py`（调网关生成带引用回答）。
每条检索结果必须带：`document_id / title / section / page / source / url / published_at / position / score`。
`[MY DESIGN]` 我认为设计的重点不在「能检索」，而在「检索不到时怎么办」：空结果时 prompt 放的是显式占位 `（当前知识库没有检索到与该问题相关的资料）`，策略要求回答「当前知识库没有足够信息」；这条行为在**离线 mock 里也照实现并被测试断言**。
我还把它包成 Agent 工具 `knowledge_search`，所以 Agent 检索与 `/api/knowledge/search` 是同一个实现，citation 能一路活到最终回答。

#### My Project Evidence

- `app/rag/{ingest,extractor,chunker,retriever,pipeline,prompt,store,schemas}.py`（约 1.1k 行）
- `app/services/knowledge_service.py`（组合 ingest / documents / search 三个用例，可注入临时 Chroma 与 mock embedding）
- 当前语料：6 篇公开文档 / 45 个 chunk（`GET /api/knowledge/documents`）
- 测试：`tests/unit/test_{chunker,ingest,retriever,pipeline,embeddings}.py` + `tests/integration/test_knowledge.py`

#### Follow-up Questions

- 你和 fine-tuning 的边界在哪？（Q7-11）
- 检索质量怎么量化？（Q7-12）
- 表格、图片、公式怎么办？（当前按文本处理，是我的已知弱点）

#### Pitfalls

- 不要把 RAG 说成「向量搜索」；它的一半是回答策略与引用契约。
- 不要说「RAG 消除了幻觉」。它让无据编变更难发生、且发生后**可追责**。

#### Interview Keywords

`grounding` `citation` `explicit refusal` `same impl as tool`

---

## Q7-02 为什么企业知识库适合 RAG？

#### Short Answer

因为企业知识的三个特征——会变、有权威版本、有权限——正好是微调很难处理而 RAG 处理得好的三件事。

#### Standard Answer

① **会变**：制度、操作规程、应急预案是版本化且频繁修订的。放进权重意味着每次修订都要重训；放进语料库意味着重新 ingest 即可。
② **有权威版本与出处**：企业里「答案对不对」经常等价于「你引的是哪份文件哪一条」。`[MY DESIGN]` 所以我每条结果都带 `title/section/page/source/url/published_at`，答案必须 `[n]` 引用。在安全与合规语境里这不是加分项，是入场券。
③ **有权限**：权重没法按用户裁剪，检索可以——检索层天然可以按 principal + ACL 过滤（`[PRODUCTION_NEXT]`；我在 Demo 里**没有**做文档级 ACL，见 Q7-14）。
④ **数据不能出去**：私有化部署时手上模型不是最强的，`[INFERENCE]` 「中小私有模型 + 好的检索与引用」通常优于「强模型 + 无资料」，因为企业问答更吃「有据」而不是「博学」。这条我会标注为需要在我自己的评测集上验证的判断。
⑤ **冷启动友好**：企业有大量已经写好的文档，但没有标注好的训练集。RAG 的输入直接就是现存资产。
⑥ **可运维**：答错了可以定位到「哪份文档该改」，知识库于是变成一个有 owner、有版本、有回归的资产，而不是一个黑箱权重。

#### Follow-up Questions

- 什么时候不该用 RAG？（结构化数值查询用工具/SQL；确定性规则判定用代码；纯风格/格式问题用 prompt；实时状态用接口而不是文档）
- 文档质量差会怎样？（垃圾进 → 带引用的垃圾出，所以内容治理先于技术）

#### Pitfalls

- 不要说「RAG 就是给模型加记忆」。它是「有据可依」，不是「记得住」。
- 不要跳过内容治理：谁批准入库、谁是 owner——面试官一定会问。

#### Interview Keywords

`versioned truth` `provenance` `ACL at retrieval time` `uses existing assets`

---

## Q7-03 chunk 怎么切？

#### Short Answer

两段：先按 Markdown 标题切成「章节块」（一个 chunk 不跨节，并携带 section 路径），再对超长块按句子边界滑窗切。块 1000 字、overlap 150。

#### Standard Answer

`[MY DESIGN]` `app/rag/chunker.py`：
① `split_markdown_blocks()`：逐行扫描并维护**标题栈**——遇到新标题就 flush 当前缓冲为 `TextBlock(text, section)`，并把栈里层级 ≥ 当前标题的条目弹出，再压入新标题；`_section_path()` 把 level ≥ 2 的标题拼成 `"A > B"` 作为 section（level-1 视为文档标题）。这样每块天然属于一个章节，且自带可引用的位置。
② 超过 `chunk_size` 的块：`split_sentences()` 按 `。！？；!?;\n` 切，`sentences_with_continuations()` 把不以终止符结尾的碎片并回前一句（避免半句被切断），再按窗口累加并保留 `chunk_overlap`。
③ 参数：`RAG_CHUNK_SIZE=1000`、`RAG_CHUNK_OVERLAP=150`（对应 SPEC 6.2 的 800–1200 / 100–200，中文按字符计）。
④ 落库 metadata：`document_id/title/section/page/source/url/published_at/position`；PDF 走 `extract_pdf_blocks()` 带页码，所以引用能指到页。
为什么是 1000 字：中文 1000 字大致装得下一条完整的操作条款或一段披露要点；同时 top_k=5 时上下文约 5000 字，不撑爆窗口。这个数字我会用评测集去调，不是信仰。
**已知弱点（我主动说）**：Markdown 表格/公式/代码块目前按普通文本处理（表格会被切成一行行 `|` 分隔），设备手册和参数表密集的场景会先在这里掉质量。

#### My Project Evidence

- `app/rag/chunker.py`（`_HEADING_RE`、`_section_path`、`split_sentences`、`DEFAULT_CHUNK_SIZE=1000`、`DEFAULT_CHUNK_OVERLAP=150`）
- `app/rag/extractor.py`（`MARKDOWN_SUFFIXES/TEXT_SUFFIXES/PDF_SUFFIXES`、`parse_front_matter`、`UnsupportedDocumentError`）
- `tests/unit/test_chunker.py`（7）+ `tests/unit/test_ingest.py`（14，含跳过 README 与不支持类型）
- 实测：6 篇文档 → 45 chunk（约 7.5/篇）

#### Follow-up Questions

- 为什么不用固定 token 数或语义分块？（token 需要真实 tokenizer，语义分块代价高且难解释；标题在正式文档里本来就是人类定义的语义单元）
- chunk 太大/太小分别坏在哪？（大 → 噪声挤掉引用；小 → 丢上下文，模型读到半句会自己补）
- SOP 的条款编号怎么在引用里保留？（把编号进 section 路径或 metadata 字段，引用显示「第 4.2 条」——这是我下一步要加的）

#### Pitfalls

- 不要说「越小越精确」：太小会丢上下文，反而制造幻觉。
- 不要假装处理了表格/图片。

#### Interview Keywords

`heading-aware chunking` `section in citation` `sentence boundary + overlap` `tables are a known gap`

---

## Q7-04 为什么需要 overlap？

#### Short Answer

因为一个完整语义经常正好被切在边界上。overlap 让边界附近的句子在相邻两块里都出现一次，避免「切分点不巧」导致证据被彻底丢掉。

#### Standard Answer

我的 overlap = 150 字 / 块 1000 字 ≈ **15%**。
机理：如果关键句横跨切分点，无 overlap 时两块各含半句，两侧都可能低于 `min_score` 而被丢——结果是**知识明明在库里，却回答「没有足够信息」**。这是最难排查的一类问题，因为看起来像「检索没召回」。
代价我也算清楚：① 索引膨胀约 15%（向量条数与扫描成本同比例）；② 同一内容可能被检回两次，占用 top_k 名额，所以 top_k=5 实际只有 3–4 条不同证据；③ 模型可能把同一段当成「两条独立证据」互相印证（错误自信的来源）。
`[PRODUCTION_NEXT]` 比继续调 overlap 更有效的是：**按 `document_id + position` 做相邻块合并/去重**——把连续命中的块拼成一条证据，同时保留引用编号。我在 metadata 里已经存了 `position`，正是为这一步留的。

#### My Project Evidence

- `app/rag/chunker.py`（窗口 + overlap）、`app/config.py::rag_chunk_overlap`
- `app/rag/retriever.py`（`OVER_FETCH=4` 过取 + 融合重排，缓解 top_k 被重复占用）
- `app/rag/schemas.py`（`RetrievedChunk.position`）
- `tests/unit/test_chunker.py`（overlap 行为断言）

#### Follow-up Questions

- overlap 会不会让引用重复？（会，所以要按 position 合并——我已经预留了字段）
- 你怎么判断 overlap 有效？（评测集上统计「边界丢失」类 case 的召回改善）

#### Pitfalls

- 不要说「overlap 是最佳实践所以要加」。要给出它防的是哪种失败模式，以及它的代价。
- 不要说 overlap 越大越安全：它会同时放大索引成本与重复证据问题。

#### Interview Keywords

`boundary loss` `15% ratio` `dedup by position next` `index inflation`

---

## Q7-05 top_k 怎么选？

#### Short Answer

从任务反推：够回答就行，宁少勿多。默认 5，接口允许覆盖（search 1–20、工具 1–10），判据是「引用正确率不再上升就说明多了」。

#### Standard Answer

`[MY DESIGN]` 配置：默认 `RAG_TOP_K=5`；`/api/knowledge/search` 的 `top_k` 允许 1–20（`MAX_TOP_K=20`）；`knowledge_search` 工具参数 1–10、默认 5。
实际检索时我**过取**：`OVER_FETCH=4`，即取 `min(top_k*4, MAX_CANDIDATES=200)` 条候选，融合打分重排后截 top_k，再按 `rag_min_score=0.10` 过滤。
为什么过取：我的 lexical 信号（CJK bigram 重合率）能把向量排名靠后的真正相关项提上来；如果只在向量 top_k 内重排，提升空间被卡住。
为什么要 `min_score` 硬过滤：**宁可少给证据，也不给无关证据**。塞进 prompt 的无关块会同时伤害两件事——模型引错来源的概率，以及「看起来有据」的误导性。
选 k 的流程（`[PRODUCTION_NEXT]`）：① 评测集看「金标证据是否进 top-k」→ 决定下限；② 看引用正确率/幻觉率随 k 的变化曲线 → 取拐点左侧；③ 若需要 k>10 才够召回，说明该上 rerank 或上下文压缩，而不是硬塞。
为什么做成**按调用可覆盖**：「恒光主要有哪些业务」（要广度）和「某条制度 3.2 款原文是什么」（要精度）需要的召回宽度不同。

#### My Project Evidence

- `app/rag/retriever.py`（`VECTOR_WEIGHT=0.5 / BODY_WEIGHT=0.25 / HEADER_WEIGHT=0.25`、`OVER_FETCH=4`、`MAX_CANDIDATES=200`、`score >= min_score` 过滤）
- `app/api/knowledge.py::MAX_TOP_K=20`、`app/agent/tools/knowledge.py::KnowledgeSearchArgs(top_k ge=1 le=10)`
- `app/config.py::rag_top_k / rag_min_score`
- `tests/unit/test_retriever.py`（8 个测试）

#### Follow-up Questions

- k 从 5 加到 20 你最担心什么变坏？（引错来源与噪声挤占，以及成本）
- 上 rerank 和加大 k 你选哪个？（先 rerank：加大 k 会把无关内容推进 prompt，rerank 是在同样上下文预算内选更好的）
- 你怎么知道现在 5 不够？（不知道——所以我要先做评测集。这是我不会假装的地方）

#### Pitfalls

- 不要说「k 越大越全越好」。
- 不要说「我做过调参实验」——我做的是「合理取值 + 全部可调 + 过取与阈值机制」，实验是 `[PRODUCTION_NEXT]`。

#### Interview Keywords

`recall@k vs citation precision` `over-fetch then fuse then gate` `per-call override`

---

## Q7-06 embedding 是什么？

#### Short Answer

把文本映射成固定维度向量，让语义相近的文本在向量空间里距离近，从而一次相似度查询就能从大量片段里召回候选。

#### Standard Answer

我的管线里 embedding 有两处：ingest 时 `embed_documents()`（批量给 chunk 建向量），查询时 `embed_query()`（把问题映射到同一空间）。抽象是 `app/embeddings/base.py` 的 `EmbeddingProvider`，两个实现：
① `MockEmbeddingProvider`（默认）：文本切成 **CJK 字符 bigram + 拉丁/数字 token**，用 blake2b 哈希到 `EMBEDDING_DIMENSIONS=1024` 个桶、L2 归一化。它**没有语义，只有词面相似性**——够验证管线，不够宣称检索质量。有个刻意的细节：只用 bigram 不混单字，因为单字在中文里太密，会让任何两篇文档都像相似，反而淹没真正的相关项。
② `OpenAICompatibleEmbeddingProvider`：打 `/embeddings`，支持 OpenAI / DashScope 兼容 / SiliconFlow / Ollama 等，`dimensions=0` 表示以 API 返回值为准，`batch_size=32` 批量。
`[MY DESIGN]` 关键约束：**向量永远由 EmbeddingProvider 显式传入，集合不使用 Chroma 内置 embedding function**（`app/rag/store.py` 的类注释里写明了）。所以「换 embedding 模型」是平台配置，不是向量库配置；也保证离线零下载、测试可复现（`tests/unit/test_embeddings.py` 断言确定性与归一化）。
`[PRODUCTION_NEXT]` 换真实 embedding 后必须**全库重灌**（不同模型的向量不可比），因此要「collection 别名 + 双索引切换」，不能停服重建；并且维度、归一化约定、query/document 是否同模型同版本，都要写进配置并做启动校验。

#### My Project Evidence

- `app/embeddings/{base,mock,openai_compatible}.py` + `build_embedding_provider()`
- `app/rag/store.py`（不用内置 embedding function）
- `tests/unit/test_embeddings.py`（9 个测试）
- `EMBEDDING_DIMENSIONS=1024` 的理由写在 `.env.example` 注释里（1024 维下相关/不相关分离度够用）

#### Follow-up Questions

- 中文 embedding 选型看什么？（语料域匹配、维度与成本、长文窗口、与 rerank 的配合、是否开源可私有化）
- 为什么 mock 也能让演示「看起来像回事」？（词面相似 + 我的 lexical 融合；语料只有 6 篇。规模上去后这点必然暴露——我主动说）
- 换 embedding 时旧数据怎么办？（双索引 + 别名切换 + 灰度对比）

#### Pitfalls

- **绝对不要拿 mock embedding 的检索效果当真实效果汇报**。这是我必须主动划清的一条线。
- 不要说「维度越大越好」：维度影响碰撞率与成本，不是语义质量的保证。

#### Interview Keywords

`offline deterministic embeddings` `provider-owned vectors` `reindex on model swap` `hash-ngram ≠ semantics`

---

## Q7-07 vector database 做什么？

#### Short Answer

存 chunk 的向量与 metadata、提供近似最近邻检索。它是**索引**不是数据源——原始文档才是真相源，向量库必须可重建。

#### Standard Answer

`[MY DESIGN]` `app/rag/store.py::VectorStore` 是**全项目唯一 import chromadb 的模块**（文件第一行的文档字符串就这么声明），能力就四件：`get_or_create_collection`、`add`（`UPSERT_BATCH=256` 分批）、`query(embedding, n)` → `VectorHit(chunk_id, text, metadata, score)`、`count/delete`。集合 `hengguang_knowledge`，路径 `./data/runtime/chroma`（PersistentClient，挂 Docker 卷）。
「索引可重建」这条原则我在代码里是照做的：`rebuild=True` 清空重灌；原文来自 `data/documents/`，元数据来自 front matter。所以在生产上我能对「索引丢了怎么办」给出确定答案：**丢索引可以，丢文档不行**。
我不指望它做的事：权限过滤、精确关键词匹配、跨库去重、排序策略——这些都在 `retriever.py` 与 metadata 层，向量库只负责「给一个向量，返回最近的 N 条」。
诚实的限制：① 这里是**单进程嵌入式** Chroma，多副本共享同一目录不是我被验证过的能力；② 1024 维 + hash-ngram mock 只保证管线跑通，不保证语义质量；③ 我没有做向量库的备份策略（生产必须有）。
`[PRODUCTION_NEXT]` 上规模后我要它给的能力，按重要性：metadata/布尔过滤（ACL 与时间范围）→ 混合检索或能与 BM25 融合 → 索引版本与别名（灰度换模型）→ 备份/快照 → 多副本与分片（只有数据量或 QPS 到了才值得）。

#### My Project Evidence

- `app/rag/store.py`（`VectorHit`、`UPSERT_BATCH`、`PersistentClient`）
- `app/rag/ingest.py`（`rebuild`、`IngestReport{documents,chunks,skipped,errors}`、`summarize_documents`）
- `tests/integration/test_knowledge.py`（ingest → documents → search 全链路）
- Docker 验证：`stop && up -d` 后文档数/chunk 数不变（`README.md`）

#### Follow-up Questions

- 文档删了但索引没删会怎样？（孤儿 chunk 仍会被召回并带引用 → 危险；我需要对账任务）
- 为什么不用 pgvector 一张表搞定？（Demo 阶段不引额外服务；生产上如果已经在 Postgres 上做 ACL 与元数据，pgvector 会显著降低组件数，这是我真实会评估的方案）
- 索引与文档一致性怎么校验？（定期 diff「文档清单 vs 索引内容」，孤儿/缺失报警）

#### Pitfalls

- 不要说「向量库能做权限过滤所以安全」。metadata 过滤只是机制，强制授权必须服务端做。
- 不要说「重建很快」：重建期检索要么停要么读半新半旧，生产要双索引。

#### Interview Keywords

`index is reproducible` `single integration module` `metadata carries citation` `orphan chunk risk`

---

## Q7-08 如何减少 hallucination？

#### Short Answer

四层：给少而准的证据、prompt 里写死回答策略、答案必须落到 `[n]` 引用、无依据强制拒答；再加一层可追责的评测。

#### Standard Answer

`[MY DESIGN]` 我在代码里做的四件事：
① **收紧上下文**：`rag_min_score=0.10` 过滤 + top_k=5。无关证据是幻觉的直接燃料，因为它让模型以为「这些里总有一个是答案」。
② **策略写进 prompt**（`app/rag/prompt.py::RAG_SYSTEM_PROMPT` 六条）：优先只用资料中出现的事实；资料不足必须明确说「当前知识库没有足够信息」，不编造数据；**不得虚构任何数字、产能、财务指标或产品名称**；用 `[编号]` 标注引用；**区分事实 / 推测 / 建议**，对后两者要明确说明；本项目只使用公开资料、不构成投资建议。
③ **让引用可机器校验**：context 块用固定格式 `[n] 标题 > 章节`，答案里的 `[n]` 必须能对上 `sources[]` 里的 document_id/section/url——「有没有据」于是变成一个可检查的属性，而不是一种观感。
④ **拒答路径有测试**：无依据时的话术（「没有足够信息 + 先 ingest 或换问法」）在 `tests/unit/test_pipeline.py`、`tests/integration/test_knowledge.py` 里被断言，也就是说它不是靠 prompt 祈祷，而是有回归保护。
`[PRODUCTION_NEXT]` 再加三件：**引用一致性检查**（答案里出现的数字/单位必须能在被引片段中找到，不通过就退回重生成或降级为「仅列资料不作答」——这一项可以纯规则实现，是我最想先做的）；**低置信度走人审**；**评测集上跟踪幻觉率**，并把每一次线上幻觉沉淀成一条永久回归样本。
一句话总结我的态度：**幻觉不能被消除，只能被变成可发现、可追责、可回归的东西。**

#### My Project Evidence

- `app/rag/prompt.py`（`RAG_SYSTEM_PROMPT`、`NO_CONTEXT_BODY`、`format_context`）
- `app/agent/prompts.py`（Agent 侧同样禁止编造 + 禁止假装调用不存在的工具）
- `app/rag/retriever.py`（分数阈值）
- `data/documents/*.md` 每篇 front matter 带 `source` + `url` + `published_at`，引用天然可核
- `tests/unit/test_pipeline.py`（9）

#### Follow-up Questions

- 真实模型一定遵守这个策略吗？怎么验证？（不一定 → 所以需要评测集 + 输出侧规则校验，把「遵守 prompt」变成可测量而不是假设）
- 「区分事实/推测/建议」模型不遵守怎么办？（结构化解耦：事实来自工具与检索、推测与建议由平台模板显式分区渲染）
- 拒答太多业务方会不满，怎么平衡？（把空召回 top query 变成知识库补料清单，同时给「该问谁」的兜底入口）

#### Pitfalls

- 不要说「加了 RAG 就没有幻觉」。
- 不要承诺「引用 100% 准确」：我现在保证引用结构存在，不保证语义映射完美。

#### Interview Keywords

`grounded prompt policy` `machine-checkable citation` `tested refusal` `fact/speculation/advice labels`

---

## Q7-09 为什么 citation 很重要？

#### Short Answer

因为在企业里一个没有出处的答案不可采信、不可复核、也不可追责。citation 把「AI 说了什么」变成「AI 依据哪份文件的哪一条说了什么」。

#### Standard Answer

`[MY DESIGN]` 我的引用链是端到端打通的（这是我最愿意现场演示的一条线）：
```
front matter(document_id/title/source/url/published_at)
 → chunker 保留 section 路径
 → Chroma metadata(+position/page)
 → RetrievedChunk
 → Citation(index,label,marker)
 → format_context() 输出「[1] 标题 > 章节」块
 → 答案里出现 [1]
 → sources[] 数组（index/document_id/title/section/page/source/url/score/citation）→ 前端渲染成可点开来源
```
`knowledge_search` 工具复用同一个 context 块，所以引用能穿过 Agent loop 活到最终回答（`AgentRunResult.sources`）。
它支撑三件具体的事：
① **业务专家 10 秒判断对不对**（打开那份文件那一条就行）——内部平台靠信任活着，这一步是信任的兑现机制；
② **安全/合规可追溯**：谁在什么时候依据哪版制度得到什么建议；
③ **反向定位该改哪份文档**：引用错了常常意味着文档本身有问题或缺失，这让知识库变成可运维资产。
`[PRODUCTION_NEXT]` 还要补：引用**双向校验**（答案中的数字必须出现在被引片段中）、**版本与生效日期必须显示**（引用一份已废止的制度比不引用更危险）、点击直达原文（内网文档系统定位）、以及把「引用为空」做成独立监控指标。

#### My Project Evidence

- `app/rag/schemas.py`（`Citation.from_result`）、`app/rag/retriever.py::build_citations`
- `app/api/knowledge.py::SearchResult/Citation`、`app/api/agents.py::AgentSourceOut`
- `tests/integration/test_web_console_contract.py::test_cited_run_carries_every_source_field_the_ui_renders`
- `DEMO_SCRIPT.md` Step 3 / Step 7

#### Follow-up Questions

- 多份文档互相冲突时怎么显示？（并列引用 + `published_at` + 「以最新版/主管部门解释为准」，模型不做裁决）
- 假引用（引了但不是支撑来源）怎么发现？（引用一致性检查：答案中的实体/数字与片段文本求交）
- 用户根本不看引用怎么办？（把引用做成答案的第一屏结构而不是脚注；统计点开率作为质量信号）

#### Pitfalls

- 不要说「citation 保证答案准确」——它保证的是**可核查性**。
- 不要暗示能跳转到内部文档：我的 `url` 来自公开语料的 front matter，指向公开页面；内网定位是 `[PRODUCTION_NEXT]`。

#### Interview Keywords

`end-to-end provenance` `reviewable in 10 seconds` `doc-ops feedback loop` `version + effective date`

---

## Q7-10 没有召回结果怎么办？

#### Short Answer

不猜、不自创兜底答案：明确说「当前知识库没有足够信息」，并把下一步动作告诉用户（补哪类资料 / 换问法 / 该找谁）。同时把空召回当成运营信号收集起来。

#### Standard Answer

`[MY DESIGN]` 三层：
① **检索层**：低于 `min_score=0.10` 的候选直接丢弃，所以空结果是**合法状态**而不是异常；
② **prompt 层**：空结果时 `format_context()` 输出显式占位 `（当前知识库没有检索到与该问题相关的资料）`，策略要求据此回答「没有足够信息」；
③ **实现层**：`MockProvider` 识别这个占位并返回固定话术「当前知识库没有足够信息回答该问题。请先通过 `POST /api/knowledge/ingest` 导入相关公开资料，或换一种问法。」——所以「拒答」是被测试断言的行为（`tests/unit/test_pipeline.py`、`tests/integration/test_knowledge.py`）。
`[PRODUCTION_NEXT]` 上线时还要处理三件我现在没做的：**区分「我不知道」和「你没权限」**（后者的措辞不能让用户误以为知识缺失，也不能泄露「有这份文档但你看不到」）；**把空召回记成运营指标**（高频空召回 = 知识库缺料清单，是补料的第一优先输入）；**给出人工兜底入口**（该问哪个 owner / 转人工）。

#### My Project Evidence

- `app/rag/prompt.py`（`NO_CONTEXT_BODY` 占位 + 六条策略里的「资料不足必须明确说明」）
- `app/rag/retriever.py`（`score >= settings.rag_min_score` 过滤）
- `app/api/knowledge.py::_require_content`（409 + details 指向 ingest 端点）
- `app/gateway/mock.py::_grounded_answer`（空/无依据时的固定拒答话术）
- `tests/integration/test_web_console_contract.py::test_empty_collection_answers_conflict_not_crash`

#### Follow-up Questions

- 拒答率和「有用性」怎么平衡？阈值谁定？（阈值应由业务方按场景接受度共同定，安全类场景宁严；工程侧提供可调旋钮与指标）
- 部分召回（召回到但不相关）怎么办？（比空召回更危险，因为会产生假引用 → 需要引用一致性检查）
- 权限导致的空召回怎么措辞？（「当前条件下没有找到可用资料」，既不泄露存在性也不误导）

#### Pitfalls

- **不要说「没检索到就用模型自身知识补答」**。企业知识场景里这是最坏答案，也是我明确拒绝的设计。
- 不要把 409（平台状态）和「没有足够信息」（回答内容）混为一谈——这两条路径我刻意分开实现。

#### Interview Keywords

`explicit refusal` `no-fill-in` `empty corpus is 409` `recall-zero as backlog input`

---

## Q7-11 RAG 和 Fine-tuning 区别？

#### Short Answer

RAG 改的是「模型这次能看到什么」，fine-tuning 改的是「模型本身会什么」。前者可更新、可追溯、可按人裁剪；后者能把风格与格式内化，但难更新、难追责、易灾难遗忘。

#### Standard Answer

| 维度 | RAG | Fine-tuning |
|---|---|---|
| 更新成本 | 重新 ingest（分钟级，我实测过） | 重训 + 重评 + 重部署 |
| 出处/引用 | 天然可给（document_id + section + url） | 知识进了权重，说不清来源 |
| 权限裁剪 | 检索时按 principal 过滤 | 权重无法按用户区分 |
| 事实精确性 | 取决于语料质量，错了好定位 | 数字类最危险，且错得自信 |
| 适合什么 | 私有知识问答、制度检索、数据解释 | 固定格式/风格、术语理解、分类抽取、用私有小模型降本 |
| 风险 | 检索不到就拒答（可控、可见） | 幻觉更难发现（像是内化了） |
| 冷启动 | 用现成文档即可 | 需要标注/构造样本 |

**我在这个场景的排序**：`[INFERENCE]` 面向「制度 / SOP / 设备文档 / 经营数据」的内部平台，第一阶段一定是 **RAG + 工具**，因为需求是**可追责的正确**，而这三类知识都会变、都有权威版本、都有权限。
**什么时候我才会考虑微调**：任务形态已经稳定、样本量足够、并且我能说清「微调要改善哪个可测指标」。典型两类：① 固定格式产文（周报、整改通知草稿）——用轻量微调固化格式比塞十个 few-shot 便宜；② 把某个高频的**分类/抽取**任务从旗舰模型降到私有小模型以省成本（这通常也是私有化落地的必经一步）。
一个常被混淆的点：**embedding 微调也是 fine-tuning**。如果领域术语让通用 embedding 召回不好，我会先动检索侧（换/微调 embedding、加 rerank、加 hybrid、修 chunk），而不是去动生成模型——检索侧的改动可测、可回滚、代价低。
`[PRODUCTION_NEXT]` 还有第三种更便宜的「个性化」：把历史优质问答对当成一类**可检索语料**（few-shot 检索 / example mining），效果接近轻量微调、风险与成本远低于训模型，而且每条示例仍可引用与下线。

#### My Project Evidence

- `[MY DESIGN]` 语料可重灌：`app/rag/ingest.py`（`rebuild` + `IngestReport`），换 embedding 模型的工程动作就是「重灌 + 双索引切换」的前半段我已经有了
- `[MY DESIGN]` 输出格式约束在 prompt 而非权重：`app/rag/prompt.py`、`app/agent/prompts.py`
- `[MY DESIGN]` 引用与来源是响应契约的一部分：`app/api/knowledge.py::SearchResult`、`app/agent/models.py::AgentRunResult.sources`

#### Follow-up Questions

- 几千份文档什么时候值得蒸馏成小模型？（当某一类任务的调用量与格式稳定性都能量化，且评测集上小模型已达标的条件下）
- LoRA 的风险你怎么控？（版本化 adapter + 上线前评测集回归 + 保留「退回 RAG-only」开关）
- 如果模型把内部知识记进了权重，安全上意味着什么？（**权重本身成为敏感资产**：泄露面变了，要按密级管理、要有下线与销毁流程）

#### Pitfalls

- 不要说「微调太高级所以我们不做」，要给判据（任务稳定性、样本量、可追责需求、可测指标）。
- 不要说「RAG 一定比 fine-tuning 好」：格式与风格类任务上微调往往更省更稳。
- 不要把「我们用了 RAG」当成技术含量的证明；难点在权限、引用一致性和内容治理。

#### Interview Keywords

`RAG = what it sees` `FT = what it knows` `provenance is the tiebreaker` `tune retrieval before generation`

---

## Q7-12 如何评估 RAG？

#### Short Answer

分两段评：检索段看 recall@k / MRR / 引用命中率，生成段看忠实度（是否只依据资料）、正确性、拒答准确率；整体看 P95 延迟与单问成本。所有指标都必须挂在一份与语料快照同时锁版的评测集上。

#### Standard Answer

**以下全部是 `[PRODUCTION_NEXT]`（我会怎么做），不是「我做过」**——这一段我准备时特意把标签写死，因为它是最容易被面试官当作吹牛的段落。
① **检索段（最便宜、最先做、可全自动）**
金标 = 每个问题标注「哪些 document_id + section 能回答」。指标：`recall@k`（证据进没进前 k）、`MRR`（排第几）、`citation precision`（前 k 里有几条真有用）、`空召回率`。
这层能直接指导 chunk_size、top_k、融合权重、要不要 rerank——**大部分 RAG 问题在检索段就能定位**，不必等到看答案。
② **生成段**
`faithfulness`：答案里每个事实断言是否出现在被引片段中。**数字/单位/产品名可以纯规则严格查**，这是我最有信心先自动化的一项，也是对幻觉最有杀伤力的一项；
`answer correctness`：对照金标要点的覆盖率；
`refusal accuracy`：**两个方向都要测**——该拒的时候拒了没（不足就会编）、不该拒的时候拒了没（过度拒答平台就没人用）；
`citation validity`：`[n]` 是否指向真正支撑该句的片段（假引用检测）。
③ **系统段**：P50/P95 延迟、失败率、工具调用成功率、单问 token 与成本。我这层已埋好一半：`metrics` 有 `requests_total / requests_by_endpoint / latency_ms_sum / tool_call_count / tool_error_count / permission_denied_count / agent_runs_by_status / error_by_code`，缺的是 token/成本维度。
④ **运营段（最常被忽略，但决定生死）**：点踩率与反馈文本、空召回 top query（=补料清单）、被引用最多的文档（=该重点维护的资产）、**过期文档命中比例**（制度过期比没制度更危险）。
**方法**：固定评测集 → 每次改动跑回归 → 记录指标差 → 立规矩：**「一个指标变好」不能以「忠实度变差」为代价**。
**现状**：`[MY DESIGN]` 我有的是**确定性回归**——423 个测试保证管线行为不漂移（拒答话术、引用字段、top_k、min_score、工具参数校验、权限拒绝），**不是**质量评测。我绝不把「测试全过」说成「RAG 效果好」。

#### My Project Evidence

- 已有确定性基础：`tests/unit/test_{chunker,retriever,pipeline,ingest,embeddings}.py`、`tests/integration/test_knowledge.py`、`test_web_console_contract.py`（30 个契约测试）
- 已有观测底座：`app/observability/metrics.py`、`app/observability/audit.py`（每次问答可按 request_id 完整复盘）
- 缺口：无评测集 / 无 judge / 无 token 成本指标（→ §22）

#### Follow-up Questions

- 只有 30 条样本你信吗？（信趋势不信绝对值；先做能规则判分的子集，比做 500 条主观标注更有性价比）
- LLM-as-judge 的偏差怎么控？（固定 judge 模型与 prompt、成对比较优于打绝对分、人工抽检校准、把 judge 自己也纳入回归）
-  recall@10 很好但答案质量没变好，可能是什么原因？（上下文里无关块挤掉了关键块 / chunk 边界切碎关键句 / prompt 策略未被遵守 → 三个方向分别对应 rerank、chunker、评测）

#### Pitfalls

- 不报任何编造的分数。
- 不要把「加测试」和「做评测」混为一谈（这是我刻意分开的两件事）。
- 不要只评答案不评检索：检索没到位时，答案指标的方差毫无解释力。

#### Interview Keywords

`recall@k first` `faithfulness by rules` `refusal both directions` `eval set versioned with corpus` `empty-recall as backlog`

---

## Q7-13 如果文档更新怎么办？

#### Short Answer

目标形态是按 `document_id` 增量重灌（删旧块 → 分块 → 嵌入 → 写入，单文档原子）+ `published_at`/版本随文档走；生产上还要有双索引别名切换与一致性对账，不能靠人工记得重跑。

#### Standard Answer

`[MY DESIGN]` **我现在能做什么**：`POST /api/knowledge/ingest`（admin + `knowledge:ingest`）→ `DocumentIngester.ingest_directory(root, rebuild=…)`；`rebuild=True` 清空集合后全量重建；元数据来自每篇的 YAML front matter（document_id/title/source/url/published_at）。
**当前限制我不掩饰**：只有全量重建，**没有暴露按文档的增量更新 API**（`store.delete(document_id=…)` 这个能力我没接到路由上）。对 6 篇文档不是问题；对 6000 篇就是——重灌期间检索要么空窗、要么读到半新半旧的索引。
`[PRODUCTION_NEXT]` 更新链路的六件事：
① **文档身份稳定**：`document_id` 由权威源（DMS/文档系统 ID）决定，不由文件名决定——否则改个名就变成「新文档 + 孤儿旧块」；
② **增量 upsert**：按 `document_id` 删旧块 → 分块 → 嵌入 → 写入，**单文档原子**（失败不留半套）；
③ **版本与时间**：`published_at` + `version` 进 metadata，默认引用最新版，同时能回答「上一版怎么写的」（制度演进是高频真实问题）；
④ **一致性对账任务**：定期比对「文档清单 vs 索引内容」，报**孤儿 chunk**（文档已撤但索引还在）与缺失项——**过期制度被引用是安全事故**，这条对账在我心里的优先级远高于加新特性；
⑤ **别名双索引**：换 embedding 模型或大批重建时建 `collection_v2`，切别名，读侧无感、可回滚；
⑥ **内容 owner 流程**（对应 `[FACT]` JD 第 6 条「平台使用规范」）：谁能批准某类文档入库/下线必须是流程，不是工程默认值。**工程管线越好，内容治理缺失造成的错误放大得越快。**

#### My Project Evidence

- `app/rag/ingest.py`（`ingest_directory(rebuild=…)`、`iter_document_files`、`IngestReport{documents,chunks,skipped,errors}`）
- `app/rag/extractor.py::parse_front_matter`（document_id/source/url/published_at）+ `extract_pdf_blocks`（页码）
- `app/api/knowledge.py::IngestRequest`（`path` + `rebuild`，admin-only）
- `tests/unit/test_ingest.py`（14 个测试，含 front matter 缺失/冲突时的跳过）
- `README.md` §已知限制（我自己写明了「ingest 目前全量重建（不增量）」）

#### Follow-up Questions

- 撤下一份涉密文档，你怎么确认索引里已经没有了？（按 document_id 删 + count 校验 + 对账报告 + 备份里也要有密级处理——这是我最想被问到的运维题）
- 同一文档两个版本冲突怎么办？（最新版优先 + 显示版本与生效日期 + 冲突提示，不静默覆盖）
- 更新频率跟业务怎么约定？（按文档类别分级：制度走审批触发、台账走日批、公开资料走周批）

#### Pitfalls

- **不要说「支持增量更新」**。当前只有全量重建，说错会被要求讲实现细节。
- 不要只讲技术就收尾：内容 owner 这层不解决，越快越好地错。

#### Interview Keywords

`per-document upsert` `orphan chunk reconciliation` `alias + double index` `content owner process`

---

## Q7-14 权限如何与知识库结合？

#### Short Answer

权限必须在**检索层**服务端强制，顺序是「先按身份过滤，再排相关性」。绝不能检索完之后靠 prompt 叮嘱模型「别提某些内容」——那是最典型的 fail-open。

#### Standard Answer

`[MY DESIGN]` **我现在做到的**：**端点级与工具级**权限——`knowledge:query`（GET /api/knowledge/documents、/api/knowledge/search）、`knowledge:ingest`（POST /api/knowledge/ingest）、`tool:knowledge`（Agent 里的 knowledge_search）。三把锁分别挂在 `require(...)`、工具执行器、以及「ingest 只允许 admin」。
**我没做的（我认为是这个项目最该被指出的缺口）**：**文档级 ACL**。当前 `app/rag/retriever.py` 与 `store.py` 的查询**不接收 principal**，metadata 里也没有密级/角色字段。所以如果我的语料里混进一份只对 manager 可见的文档，现在的检索会把它给所有人。我语料现在全是公开资料所以不构成实际泄露，但**这不是一个安全设计，是一个尚未需要的功能**——我会主动这样区分。
`[PRODUCTION_NEXT]` 企业知识库权限的正确做法（顺序很重要）：
① **身份来自请求，不来自模型**：`CurrentUser` → `Actor` 一路显式传递（这条链我**已经通了**，正好是能直接往上扩展的位置）；
② **ACL 落进索引 metadata**（`allowed_roles` / `allowed_departments` / `classification`），检索时**先过滤再 top_k**。反过来（先 top_k 再过滤）会有两个坏结果：有权限的内容被无权限内容**挤掉**、以及泄露排名信息；
③ **集合级隔离**处理高敏感域（研发配方、事故调查）：物理分 collection 甚至分库，而不是只靠一个 metadata 布尔；
④ **撤权要立刻生效**：ACL 缓存要有失效通道；文档下线后孤儿 chunk 必须被清扫（回到 Q7-13 的对账任务）；
⑤ **答案层再收一道**：引用渲染只显示当前用户可见的标题/摘要（标题本身可能敏感），引用链接的权限由文档系统自己判；
⑥ **可追责**：每次检索一行审计（我已有 `knowledge.search`，记 `top_k` 与命中数，**不记 query 文本**——这是刻意的最小化）；
⑦ **负例测试**：每条检索路径都要有「低权限用户 + 敏感文档 → 断言不可见」的测试。**没有负例测试的 ACL 等于没做**，因为它无法防止将来被改掉。
`[INFERENCE]` 对恒光：`[FACT]` 公开资料显示公司有怀化/衡阳/老挝三大基地及多家控股子公司（来源见 §来源，检索时间 2026-10-01）。`[INFERENCE]` 这类多基地结构下「哪些制度/台账对哪些基地可见」是真实存在的需求，所以 ACL 的位置在**第一期就要有**（哪怕先只实现 collection 隔离），第二期再补会非常痛。

#### My Project Evidence

- `app/auth/dependencies.py::require(Permission.KNOWLEDGE_QUERY / KNOWLEDGE_INGEST / TOOL_KNOWLEDGE)`
- `app/observability/audit.py`（`knowledge.search` 行的字段最小化）
- `tests/integration/test_knowledge.py` + `test_web_console_contract.py`（端点级权限与 401/403 行为）
- 缺口证据（可当场指出）：`app/rag/retriever.py::retrieve` 签名中**无 principal/ACL 参数**

#### Follow-up Questions

- 一份文档同时属于两个密级怎么办？（密级是单调格，正常只能有一个；跨域需求用 collection 隔离 + 双登记，不是一个字段塞两个值）
- 「有权限知道文档存在、但没权限看内容」要不要支持？（要，且要专门的措辞与元数据设计——这是企业文档系统的常见真实需求）
- 你怎么防「通过引用标题泄露」？（标题也过 ACL；必要时只给「有一份相关制度，请联系 owner」）

#### Pitfalls

- **绝对不要说「我们有 RBAC，所以知识库是安全的」**。我的 RBAC 是端点级的，文档级没有——被追问时必须承认。
- 不要说「用 prompt 让模型别说」能当权限用。
- 不要说「向量库的 where 过滤就是权限」：它是机制，强制授权必须在服务端代码里，并且要有负例测试。

#### Interview Keywords

`filter before rank` `principal explicit all the way` `collection isolation for high class` `negative ACL tests` `least-privilege audit fields`

---

`[PRODUCTION_NEXT]` 上线时还要处理三件我现在没做的：**区分「我不知道」和「你没权限」**（后者的措辞不能让用户误以为知识缺失，也不能泄露文档存在性）；**空召回率作为运营指标**（高频空召回 = 知识库缺料清单，是补料的第一优先输入）；**人工抽检引用一致性**（把「回答里的数字能在被引片段里找到」做成一条自动化检查 + 每周抽检一批）。

#### Interview Keywords

`filter before rank` `principal explicit all the way` `three open production gaps` `spot-check citation consistency`
# 8 · Agent

## Q8-01 Agent 与 Chatbot 的区别？

#### Short Answer

Chatbot 是「一问一答，只产出文本」；Agent 是「为达成一个目标，自己决定调用哪些工具、看结果、再决定下一步，直到给出答案或用尽预算」。

#### Standard Answer

三个可操作的差别：
① **有没有动作权**：Agent 能对外部系统产生影响（我这里全是只读查询，所以唯一的副作用是「写了一条审计行」）；
② **谁控制流程**：Chatbot 的流程写死；Agent 的下一步由模型在运行时决定——我的实现里模型可以从 4 个白名单工具里选、可以**不选**、可以在失败后换路径；
③ **状态与终止条件**：Agent 必须有显式状态与可解释的终止。我的 `AgentState` 带 `step / tool_results / sources / messages / status`，`AgentRunResult.status ∈ {completed, max_steps, max_tool_calls}`——**这三个值就是「我说得清它为什么停」**。
平台视角我更想强调一点：Agent 的难点不是让它「更自主」，而是让它的自主**可预算、可审计、可追责**。所以我做的三件事都围绕这点：白名单限制能力面、`max_steps/max_tool_calls` 限制消耗、`request_id` 让每一步可回放。
（我避免两种说法：「Agent = 会思考的程序」这种不可检验的定义；以及把多 Agent、长期记忆、规划器这些**我还没做**的能力说成做过。）

#### My Project Evidence

- `app/agent/runtime.py`（loop + 预算 + 状态机）、`app/agent/models.py`（`AgentState`、`AgentRunResult.status`）
- `app/agent/registry.py`（能力面白名单）
- `tests/unit/test_agent_runtime.py`（loop 限制、停止状态、trace 结构）
- `DEMO_SCRIPT.md` Step 3/4（现场看它自己决定调哪个工具）

#### Follow-up Questions

- 你的 Agent 有记忆吗？多轮上下文呢？（无跨请求记忆：messages 每次从 `[policy, user]` 起步 → 这是缺口，见 §22）
- 什么时候你反而建议用固定工作流而不是 Agent？（顺序确定、需要审批、有副作用时——见 Q8-10 / Q8-12）
- 怎么衡量一个 Agent 值不值得上？（对比固定流程：额外成功率增益 vs 额外延迟/成本/不可预测性）

#### Pitfalls

- 不要说「我的 Agent 会自主规划」。它是「模型选工具 + 我把结果回填」，规划能力来自模型本身，我没有 planner。
- 不要说「Agent 比 Chatbot 高级」。任务边界清楚的问答用固定流程更省更稳。

#### Interview Keywords

`action + state + termination` `bounded autonomy` `auditable step trace` `no memory yet`

---

## Q8-02 Agent Loop 如何工作？

#### Short Answer

每一步一次模型调用：模型请求 tool_calls 就全部执行并回填成 tool 消息，没请求就收尾；三个出口（final / max_steps / max_tool_calls）保证一定终止。

#### Standard Answer

`[MY DESIGN]` `app/agent/runtime.py::AgentRuntime.run()` 的实际结构：
```text
while state.status == "running" and state.step < settings.agent_max_steps:
    if len(state.tool_results) >= settings.agent_max_tool_calls:
        state.status = "max_tool_calls"; break            # 预算 ①（loop 顶部）
    state.step += 1
    response = await self.gateway.chat(state.messages, tools=self.registry.openai_schemas())
    state.trace.append(TraceStep(type="llm", ...))         # 每步都留痕
    if not response.tool_calls:
        state.final_answer = response.content or "Agent 未生成有效回答。"
        state.status = "completed"
        break
    state.messages.append(self._assistant_message(response))
    for call in response.tool_calls:
        if len(state.tool_results) >= settings.agent_max_tool_calls:
            state.status = "max_tool_calls"; break         # 预算 ②（一轮内多请求时）
        result = await self.executor.execute(call, actor=self._actor(user, request_id))
        state.tool_results.append(result)
        state.trace.append(TraceStep(type="tool_call", tool_name=..., success=...))
        if result.metadata.get("sources"): state.sources.extend(...)   # 引用跨步累积
        state.messages.append(self._tool_message(call.id, result))
        # loop 里被 break 掉时补一条 stopped trace（在 loop 外）
```
四个我认为值得讲的细节：
① **messages 就地累积**：工具结果作为 `{"role":"tool","tool_call_id":id,"content":...}` 并进同一条 `state.messages`，下一轮模型看到完整历史。串工具靠的是**上下文累积**，不是我把 A 的输出接到 B 的输入。
② **失败也回填**（`_tool_message`：失败时 content 是「工具执行失败：{error}」），所以模型有机会改参数或换工具——这是**把纠错权交回模型**，同时不牺牲边界。
③ **预算检查两处**：loop 顶部管「进入下一轮之前」，for 内管「一轮请求了 10 个工具」的情况。只有 loop 顶部一个检查是不够的。
④ **`_remember_model()`**：把 `response.model` 塞进 `Actor.extra["model"]`，只为让工具级审计行知道「这次调用是哪个模型发起的」。很小但很典型的可观测性设计。
⑤ **loop 外补 trace**：`max_tool_calls` 是在内层 break 的，如果不在 loop 外补一条 `type="stopped"`，前端时间线会「断在半路」。这是我写的时候被自己的测试逼出来的细节。

#### My Project Evidence

- `app/agent/runtime.py`（整段 loop）、`app/agent/models.py`（`TraceStep`、`ToolExecution`）
- `app/agent/prompts.py::AGENT_SYSTEM_PROMPT`（策略：不得编造、无依据要说明、不得假装调用不存在的工具）
- `tests/unit/test_agent_runtime.py`、`tests/integration/test_agent.py`
- `web/src/pages/AgentPlayground.tsx` 的 `FlowStrip` + Agent Trace 面板（照 trace 渲染）

#### Follow-up Questions

- 为什么 tool_calls 超预算时是 `break` 而不是继续？（把「预算耗尽」变成 **loop 级状态**而不是某条工具失败，这样 `status` 才可信）
- 为什么没有最终答案时不抛异常？（这是平台行为不是故障：返回 `status + 说明性 final_answer`，用户与运维都看得懂）
- 你要怎么支持多轮会话？（把 messages 外置到会话存储 + 压缩历史 + 会话级预算与权限）

#### Pitfalls

- 不要说「它会一直跑直到完成」。它有硬预算，且终止原因是响应字段。
- 不要把它说成 ReAct 实现。我做的是「tool_calls 循环 + 状态机」，**没做显式 thought 抽取**，只是把 `llm` 步骤都记进 trace。

#### Interview Keywords

`bounded loop` `tool messages backfilled` `failures are data` `status is the contract`

---

## Q8-03 Tool Calling 是什么？

#### Short Answer

模型不执行任何事：它按给定 JSON schema 输出「我想调 X 工具、参数是 Y」，由我的代码校验并执行，再把结果作为 tool 消息回灌。

#### Standard Answer
`[MY DESIGN]` 实现分三段：
① **暴露能力**：`registry.openai_schemas()` 把每个 `Tool` 转成 `{"type":"function","function":{name,description,parameters}}`，`parameters` 由 Pydantic `args_model.model_json_schema()` 生成——**单一来源，不手写第二份**。
② **模型请求**：`ModelResponse.tool_calls: list[ToolCall(id,name,arguments)]`。真实 provider 走 OpenAI 的 `tool_calls` 字段，由 `parse_tool_calls()` 归一化：缺 `id` 补 `call_N`、`arguments` 是坏 JSON 变 `{}`。容错的道理是**让畸形参数交给 executor 变成受控失败**，而不是在这里 500。
③ **执行与回填**：`ToolExecutor` 四步（白名单 → 权限 → 参数校验 → 执行），结果转成 tool 消息；失败也回填，内容是「工具执行失败：…」。
我特意让 `MockProvider` 完整实现了这个协议（识别 ERP/Safety 的问题模式 → 产出带 `arguments` JSON 的 `ToolCall`），这样**我的测试覆盖的是真实模型走的同一条消息格式**，不是只有真 provider 才跑得通。
**边界原则**：模型只能选我给的 name、只能填我允许的字段。ERP 工具最典型：`operation` 是 7 值之一的 `Literal`，`days` 是 1–365 的 int，`limit` 是 1–50，另有 material/status/category 三个可选枚举。**它没有任何办法表达「查这张表这列」。**

#### My Project Evidence

- `app/agent/tools/base.py::Tool.to_openai_schema / validate`
- `app/gateway/base.py::ToolCall`、`app/gateway/openai_compatible.py::parse_tool_calls`
- `app/gateway/mock.py::_tool_call`（脚本化 / 模式化 tool_calls）
- `app/agent/runtime.py::_assistant_message / _tool_message`
- `tests/unit/test_agent_tools.py`（17）+ `tests/unit/test_gateway.py`

#### Follow-up Questions

- 模型幻觉出一个不存在的参数会怎样？（Pydantic 拒绝 → `INVALID_ARGUMENTS`，工具不执行，摘要回灌给模型）
- 并行 tool_calls 怎么处理？（我串行执行，见 Q8-09）
- 工具多了模型选错怎么办？（按角色/意图裁剪可见工具集 → 我有 `allowed_tool_names()` 但 loop 还没用它裁剪，这是下一步）

#### Pitfalls

- 措辞要准：**模型「请求」工具，执行永远在我的进程里**。说成「模型调用工具」在安全讨论里会被抓住。
- 不要说「工具参数可信」：所有参数都要过校验（我这层是 Pydantic + executor 的 operation 白名单**各查一次**）。

#### Interview Keywords

`request not execute` `schema single source` `args validated twice` `mock implements the protocol`

---

## Q8-04 为什么 Tool 需要 schema？

#### Short Answer

三个理由：让模型知道能填什么（提高正确率）、让我能确定地校验与归一化输入（安全）、让接口成为可测试的契约（工程）。

#### Standard Answer

`[MY DESIGN]` 同一份定义在我代码里有三重身份：
① 给模型的**说明书**：`description` 里我直接把可选 operation 写全（ERP 工具描述列举 7 个 operation 并写明「数据全部为演示用合成数据」），减少瞎猜；
② 给我的**校验器**：`Tool.validate()` = `args_model.model_validate(arguments).model_dump()`。于是 `days: 0`、`limit: 999`、`operation: "drop_table"` 全部在工具执行前被拦成 `INVALID_ARGUMENTS`，而且我能给字段级错误摘要回灌（`_validation_summary`），让模型有机会改参数重试；
③ 对外的**契约**：工具清单随 `/api/models` 暴露；`/api/agent/run` 响应体字段由 30 个 Web Console 契约测试钉住，前端不会因后端漂移而崩。
最有说服力的一句：**没有 schema 就没有边界**。只靠 prompt 说「请只查这几张表」，模型输出就是一个我必须解析再祈祷的字符串；有了 schema，非法输入变成一个**可预期、可审计、可计数**的分支（`error_by_code.INVALID_ARGUMENTS`）。

#### My Project Evidence

- `app/agent/tools/base.py`（`parameters` / `validate` / `to_openai_schema`）
- `app/agent/tools/{erp,safety,knowledge,document}.py`（4 个 args_model）
- `app/agent/executor.py::_validation_summary`
- `tests/unit/test_permissions.py::test_schemas_are_generated_for_every_tool`、`test_business_operations_are_the_fixed_whitelist`

#### Follow-up Questions

- schema 严格（枚举/范围）vs 宽松（自由文本）怎么权衡？（默认严格；只有检索类 `query` 字段留自由文本，因为它语义上就该自由，且有长度约束兜底）
- 校验失败要不要把原因告诉模型？（我给。理由：能显著提升一次重试成功率；代价是暴露内部字段名——在**自家工具**上我认为可接受，**外部 server 的 schema** 我不会原样透传）
- 出参要不要 schema？（要。我目前 payload 有约定但无强制校验 → 缺口）

#### Pitfalls

- 不要说「schema 是为了让模型更聪明」。它首先是为了让**我的**校验有依据。
- 不要忽略 `description` 质量：schema 对了但描述含糊，模型照样选错。

#### Interview Keywords

`input contract` `fail early with field-level reason` `single source of truth` `schema = boundary`

---

## Q8-05 为什么限制 max_steps？

#### Short Answer

因为 Agent 最贵的失败模式是「不终止」：它持续消耗 token、时间、下游系统容量，而且没人看着。上限把不可控变成可预期。

#### Standard Answer

`[MY DESIGN]` 默认 `AGENT_MAX_STEPS=5`（一次 agent.run 最多 5 轮模型调用）；请求侧可覆盖，但硬上限 20（`MAX_REQUEST_STEPS=20`，Pydantic `le=20`）。
到顶而没产出最终答案时我**不抛错**，而是：`status="max_steps"`；`final_answer` 是一段明确说明（「Agent 已在安全限制处停止：共执行 N 次工具调用、M 步，未生成最终回答。」）；trace 里补一条 `type="stopped", detail="max_steps"`。
**为什么不抛错**：这是平台行为不是异常。用户拿到可读、可解释的结果；审计与指标正常写（`agent_runs_by_status.max_steps` 计数）。运维能看到「有一类问题在撞预算」——**这本身就是需求信号**（说明工具设计不好或问题该被拆细）。
**为什么是 5 不是 50**：我的正常链路是「模型决定调工具 → 拿到结果 → 收尾」，1–2 步就够；5 已经允许一次失败重试。留更大预算只是把故障时间变长、成本变高。
`[PRODUCTION_NEXT]` 预算要做成**三维**：步数 + token + 墙钟时间，再加**进展检测**（同工具同参数连续两次 = 无进展，提前停）；并按 agent 类型/调用方配置化，配置与触发原因都写进审计。

#### My Project Evidence

- `app/config.py::agent_max_steps`、`app/api/agents.py::MAX_REQUEST_STEPS`
- `app/agent/runtime.py`（loop 顶部预算检查 + stopped trace + 说明性收尾）
- `app/observability/metrics.py::observe_agent_run(status)`
- `tests/unit/test_agent_runtime.py`

#### Follow-up Questions

- 只有步数上限够吗？（不够：一轮可以请求多个工具 → 这就是 max_tool_calls 存在的理由）
- 预算触发算错误还是正常？（算正常终止，但要单独计数；混进 error 会让真实故障被淹没）
- 用户能不能自己调大预算？（我给到 20，这是 Demo 特权。生产上我默认**禁止外部调用方覆盖平台预算**，只允许平台按 agent 配置）

#### Pitfalls

- 不要说「无限循环不会发生」。要说「我用预算保证终止，并且终止可见、可计数、可解释」。
- 不要漏说自己缺 token/时间维度——面试官问「那它跑 5 步花 200 万 token 怎么办」时，正确答案是「现在会，这是我要补的第二件事」。

#### Interview Keywords

`guaranteed termination` `stop reason in the contract` `budget as telemetry` `three-dimension budget next`

---

## Q8-06 为什么限制 max_tool_calls？

#### Short Answer

因为步数限制的是「模型被调用几次」，工具次数限制的是「下游系统被打多少次、数据被读多少」。两者不同源，必须分开管。

#### Standard Answer
一个极端例子说明为什么两个都要：**模型一次响应里可以同时请求 10 个 tool_calls**（我的 loop 是「一轮内全部执行」）。那么 `max_steps=5` 只压住轮数，一轮 10 次工具调用完全合法——真正被压住的是工具侧。所以我在**两个位置**检查：loop 顶部（`len(state.tool_results) >= tool_budget` → 状态 `max_tool_calls`）和 for 内部（超预算 `break`，交给 loop 顶部转换成停止状态）。
默认 `AGENT_MAX_TOOL_CALLS=8`（与 `max_steps=5` 同级 env 可配）。它保护三样东西：合成的 SQLite（生产上就是 ERP 只读库）、外部系统 QPS、以及最坏情况下单次请求的成本上限。
可观测配套：`tool_call_count / tool_error_count / permission_denied_count` 三个计数器 + 每条 `tool.call` 审计行 + trace 里的 `tool_call` 步骤。所以「某类问题平均要打 6 次工具」这种事现在就能从指标看出来。
`[PRODUCTION_NEXT]` 还要加：按 agent 类型的工具配额、按用户的滑窗限流（需要共享计数器 → **这就是我第一次真正需要 Redis 的地方**）、工具级熔断（下游变慢就暂时不让它出现在可选工具里，而不是让每个请求都撞上去）。

#### My Project Evidence

- `app/config.py::agent_max_tool_calls`、`app/agent/runtime.py`（两处检查）
- `app/observability/metrics.py::observe_tool_call(success, permission_denied)`
- `tests/unit/test_agent_runtime.py`、`tests/integration/test_agent.py`
- `SPEC.md` §0.1 第 2 条（「预算限制」是本期必做项）

#### Follow-up Questions

- 8 这个数怎么来的？（Demo 里是「允许多工具一轮 + 一次重试」的经验值；生产必须由工具调用次数的 P95 分布决定，而我还没有这个数据——所以我的真实答案是「先埋数，再定值」）
- 工具次数和成本的关系怎么量化？（每次调用的读行数 → 进 prompt 的 token → 单价；网关的 `usage` 已有原始数据，缺聚合）
- 一个工具很慢会拖死整个 loop 吗？（会。现在同步等待且**没有 per-tool timeout** → 缺口，见 Q9-04）

#### Pitfalls

- 不要只说「防止失控」。要指出它和 max_steps 保护的对象不同，否则面试官认为你只上了一道保险。
- 不要声称有 per-tool timeout 或熔断——我没有。

#### Interview Keywords

`two independent budgets` `downstream protection` `loop-top + per-call check` `measure P95 then set`

---

## Q8-07 Agent 无限循环怎么办？

#### Short Answer

三层：硬预算保证一定终止；把重复/无进展变成可检测的停止理由；终止留下可追责记录而不是静默结束。

#### Standard Answer

**已有两层**：`max_steps=5` + `max_tool_calls=8`，两个检查都在真正调模型/工具**之前**，所以终止是**有保证的**（不是概率性的）。终止后有明确说明 + `stopped` trace + `status` 字段 + 指标计数。另外 `ToolRegistry` + `ToolExecutor` 保证「未知工具不会被执行」，防止模型用一个不存在的工具名反复空转。
**还缺的第三层（我列在 §22 的缺口）**：**进展检测**。当前实现不知道「这次调用和上次是不是同一个工具同一组参数」，所以理论上模型可以连续 5 次问同一个查询、每次都成功、什么也没推进。
`[PRODUCTION_NEXT]` 我会加：
① 同 `(tool, arguments)` 哈希连续重复 ≥2 次 → 提前终止，状态 `no_progress`；
② 结果集为空或与上次完全相同也计入无进展；
③ 每步记一个「已获证据量」度量，让「连续三步没增加任何证据」成为可判定的停止条件；
④ 预算维度补 token 与墙钟 deadline，**超时时带着已获得的引用先收尾**（优雅降级而不是截断）；
⑤ 终止原因写进审计与指标，做成运营信号（某类问题频繁 `no_progress` = 工具设计问题）。

#### My Project Evidence

- `app/agent/runtime.py`（两个预算检查的位置 + stopped 分支）
- `app/agent/executor.py::ERROR_UNKNOWN_TOOL`（未知工具不执行、失败回灌）
- 缺口证据：`AgentState` 里没有「上次调用指纹」字段；`ToolExecution` 有 arguments 但 runtime 不比对

#### Follow-up Questions

- 怎么区分「合理重试」和「卡住」？（看是否产生新证据：参数变了吗？结果变了吗？→ 所以我需要缓存每步的结果指纹）
- 熔断后要不要告诉用户那次没成功？（要。`status` + 说明性 final_answer + trace 三者一致，绝不给一个假装完整的答案）
- 如果 loop 里有一个写操作，超时终止了怎么办？（**未知状态**问题：只能靠幂等键 + 对账，不能自动重试 → 引出 Q9-05）

#### Pitfalls

- 不要说「设了上限就不会死循环」。上限保证**终止**，不保证**不浪费**：终止前你可能已经花了 8 次工具调用。这个区别必须说得出。
- 不要说「模型一般不会重复调」。概率不构成保证，保证来自代码。

#### Interview Keywords

`bounded termination` `no-progress detection next` `deadline + graceful stop` `stop reason is telemetry`

---

## Q8-08 Tool failure 怎么处理？

#### Short Answer

失败是一种正常输出，不是异常：结构化 `ToolResult(success=false, error, error_code)` 回填给模型让它有机会换路径，同时写审计与指标，HTTP 保持 200。

#### Standard Answer

`[MY DESIGN]` 五类失败全部在 `ToolExecutor` 一处收口：
| 失败 | error_code | 执行工具？ | 触达数据？ | HTTP |
|---|---|---|---|---|
| 未知工具 | `UNKNOWN_TOOL` | 否 | 否 | 200 |
| 未认证 / 越权 | `PERMISSION_DENIED` | 否 | 否 | 200 |
| 参数不合法 | `INVALID_ARGUMENTS` | 否 | 否 | 200 |
| operation 不在白名单 | `INVALID_OPERATION` | 是（工具内判） | 否 | 200 |
| 查询/DB 故障 | `DATABASE_ERROR` / `TOOL_ERROR` | 是 | 尝试了但失败 | 200 |
共同机制四条：
① **异常绝不逃出 executor**（`except Exception` 兜底，文件注释直接写着「the boundary that contains tools」）；
② **回灌给模型的内容可读**（`工具执行失败：{error}`），它有机会改参数或换工具；
③ **每条失败都有审计与指标**（`tool.call` 行 status=`error`/`denied` + `tool_error_count`/`permission_denied_count`）；
④ payload 里带 `error:{code,message}`，前端能直接渲染而不需要解析文本。
**为什么 HTTP 保持 200**：因为「Agent 完成了一次运行」是真的，工具失败是这次运行的**内容**。把内容级失败升成协议级 5xx 会毁掉可观测性（所有失败挤进 5xx 分布），也让前端无法区分「模型不给力」和「服务挂了」。
业务工具侧还有一层细节：`BusinessQueryTool` 把 `BusinessQueryError`（DB 层）转成 `DATABASE_ERROR`，文案是「ERP 采购数据暂时不可用（异常类型名）」——**不带 SQL、不带连接串、不带堆栈**。

#### My Project Evidence

- `app/agent/executor.py`（三码 + 兜底 + 统一审计）
- `app/agent/tools/business.py`（`_failure`、`render`、`except Exception` + `logger.warning(extra={event:"tool.error"})`）
- `app/db/queries.py::_run`（`SQLAlchemyError` → `BusinessQueryError`；日志只带类型名 + 截断 200 字符）
- `tests/integration/test_platform.py::test_tool_failure_does_not_become_a_500`
- `tests/unit/test_agent_tools.py`（17）、`tests/unit/test_erp_tool.py`（26）

#### Follow-up Questions

- 要不要自动重试？哪些能重试？（只读 + 幂等 + 明确可退避的错误才可以；写操作超时是未知状态，绝不自动重试）
- 连续失败要不要熔断？（要，`[PRODUCTION_NEXT]`：按工具维度滑窗错误率，超阈值就把该工具从可选集里摘掉一段时间）
- 所有工具都失败了，最终答案该怎么给？（现在靠模型基于「都失败了」自己收尾；生产要显式标注「本次未取得业务数据」并给补查入口——这是我能想到的最容易被忽略的一处）

#### Pitfalls

- 不要说「我们有重试」。我没有实现重试/退避，是缺口。
- 不要把 200 说成「没错误」：错误在信封里（`error_code`）+ 审计 + 指标。这是**分层**，不是掩盖。

#### Interview Keywords

`failure as data` `five controlled error codes` `no stack or SQL leak` `200 ≠ no error`

---

## Q8-09 多个 Tool 怎么串起来？

#### Short Answer

两种：模型驱动的串联（结果进 messages，模型据此决定下一步），和编排式 pipeline。我实现的是前者；一轮内多个 tool_calls 串行执行。

#### Standard Answer

`[MY DESIGN]` 具体机制：每次工具执行完，结果以 `role="tool"` 消息**并进同一条 `state.messages`**，下一轮模型看到完整历史（policy + user + assistant(tool_calls) + tool + …）。
所以「串起来」**不是**我把 A 的输出接到 B 的输入，而是**上下文累积**：模型可以基于 `knowledge_search` 返回的制度条款，再决定去查该区域的安全事件分布。
一轮内若有多个 tool_calls，我按顺序 for 循环执行（**串行**），结果按同序回填，`tool_call_id` 一一对应。
最有代表性的组合场景是 `[FACT]` SPEC 场景 D 那类问题：`knowledge_search`（制度/背景）+ `safety_incident_analysis`（数据）→ 综合回答。trace 里能看到 `llm → tool_call ×2 → llm → final`，Web Console 的时间线就是照 trace 画的。
**我为什么不做成显式图**（详见 Q8-10）：5 天里我优先保证「边界正确 + 可追溯」。显式状态图的收益（分支、并行、断点续跑）在我这个负载用不上，成本（多一层抽象、多一套状态语义）立刻要付。
**当前限制（如实说）**：① 工具间没有结构化结果传递（第二个工具只能看到第一个的**文本块**，看不到它的 payload JSON——因为回填的是 `result.content`）；② 无并行；③ 无中间结果缓存（同一轮重复查询会真查两次）；④ 无失败补偿（只读工具暂不需要）。
`[PRODUCTION_NEXT]` 一旦出现「必须严格顺序 + 条件分支 + 有副作用」的流程（例如发起一张需审批的核对单），我会把它从自由 loop 挪进**确定性工作流**：Agent 只负责产出「建议执行 X」，执行由带状态机/审批的工作流完成，人确认在流程里，审计在两处。

#### My Project Evidence

- `app/agent/runtime.py`（for 循环串行 + `_tool_message` 回填 + `state.sources.extend(...)`）
- `app/agent/tools/knowledge.py`（`metadata["sources"]` 是引用跨步累积的通路）
- `app/agent/models.py::TraceStep`
- `tests/integration/test_web_console_contract.py::test_trace_pairs_tool_calls_in_order`

#### Follow-up Questions

- 串行不并行会不会很慢？（会，`[PRODUCTION_NEXT]`：无依赖的多工具请求应 `asyncio.gather` 并行以砍 P95；但有共享写状态/限流时必须串行——我会先加只读并行）
- 工具中间结果要不要沉淀成可复用记忆？（短期：会话级缓存；长期：必须是带权限与 TTL 的检索语料，不是「模型记得」）
- 两个工具结论冲突怎么办？（**呈现冲突 + 各自引用 + 时间戳**，交给人判断；绝不让模型平均两个数）

#### Pitfalls

- 不要说「Agent 自己会编排所以不用设计」。工具的可组合性靠 schema 与 description 质量。
- 不要说「支持并行工具调用」——不支持。

#### Interview Keywords

`context accumulation not piping` `serial within a step` `sources carried across steps` `workflow for side effects`

---

## Q8-10 当前项目为什么没有直接用 LangGraph？

#### Short Answer

因为我要演示的是「平台层的决策」，而框架把这些决策藏进了它的抽象里；另外它提供的状态图、检查点、断点续跑在我这个负载上用不上，成本却立刻要付。

#### Standard Answer

`[MY DESIGN]` 三个具体判断：
① **可解释性优先**：面试里我要能回答「为什么权限检查在参数校验之前」「为什么工具失败不抛异常」「为什么超预算是 break 而不是 raise」。如果我写 `graph.add_node("executor", ...)`，这些语义是框架的，不是我的。我的 loop 约 60 行，读完就能确认它一定会终止——在安全评审语境里这是**实际价值**，不是洁癖。
② **能力用不上**：LangGraph 的价值在**图编排**（分支、并行、子图循环、检查点持久化、断点续跑）。我的场景是单 Agent、4 个只读工具、无持久会话、预算内终止。为它引入状态图引擎，等于给一个 while 循环套一层 DSL。
③ **依赖面与升级风险**：LLM 框架迭代快、API 变更多。我的运行依赖只有 FastAPI / Pydantic / SQLAlchemy / httpx / Chroma / PyYAML / pypdf，**Agent 层零第三方依赖**，所以这条风险为 0（`[FACT]` pyproject.toml 可查）。
我没有否定框架，我否定的是「不用框架就没有平台」。
`[PRODUCTION_NEXT]` 我的**上判据**（三条里中两条就上工作流引擎）：① 有没有需要**持久化的中间状态**；② 有没有需要**人审批的暂停点**；③ 有没有需要**并行的多子任务**。
`[INFERENCE]` 关于 JD：`[FACT]` 它把 Dify、RAGFlow、FastGPT、one-api/new-api、MCP 列在「研究并评估引入」那一条里。我读成：这个岗位需要的是**能判断何时用现成组件、何时自研，并且说清判据**，而不是绑定某一个框架。这正是我在这个项目里练的判断力（对照 §23 Q23-04/05/06、§28）。

#### My Project Evidence

- 依赖清单：`pyproject.toml`（无 langchain / langgraph / llamaindex）
- `app/agent/runtime.py`（自研 loop）、`app/agent/prompts.py`（策略与 loop 分离）
- 测试测的是行为不是框架：`tests/unit/test_agent_runtime.py`

#### Follow-up Questions

- 明天要你加多 Agent 协作，你先改哪里？（先把 `Actor` 与会话状态外置，再考虑 supervisor/worker；不会先改 loop 结构）
- 怎么防止自研变成「重复造轮子还要自己养」？（限定自研面：我只自研 loop + executor + 网关抽象，向量库/embedding/HTTP/DB 全部用库。这条线我划得很清楚）
- 只用 LangChain 的 provider/tool 抽象不用它的 chain，你怎么评估？（我会先看它带来的间接层是否让我能解释每一行；我的答案是先自建，等它证明能删掉我的代码而不是加我的代码）

#### Pitfalls

- **绝对不要说「框架太简单/太脏所以不用」**。要说「我的负载不需要它提供的能力，而我需要为每一行负责」。
- 不要假装读过我没读的源码。被问 API 细节时如实说「我需要在具体版本上验证」。

#### Interview Keywords

`buy vs build with criteria` `auditable 60-line loop` `zero framework deps in agent layer` `three-part escalation test`

---

## Q8-11 如果 Agent 做了错误工具选择怎么办？

#### Short Answer

分三种：选了不存在的工具、参数填错、选了合法但不合适的工具。前两种我在 executor 里已经变成受控失败；第三种只能靠描述质量、按角色裁剪工具集和评测。

#### Standard Answer

`[MY DESIGN]` **已有的三道硬防线**：
① 不存在的工具 → `UNKNOWN_TOOL`，不执行；
② 参数错 → `INVALID_ARGUMENTS`，带字段级摘要回灌（模型有改参数的机会）；
③ operation 不在白名单 → `INVALID_OPERATION`（业务工具内部**再查一次**），文案直接把可选值列出来。
再加**权限裁剪**：operator 走到 ERP 工具会被 executor 拒（`PERMISSION_DENIED`），审计留 `denied` 行。
**真正没解决的是「合法但不合适」**（用户问财务，模型调了 safety 工具）。处置办法按性价比排：
- 改 `description`（ERP 工具描述里明确列了 7 个 operation 的语义，就是为这个）；
- 改系统 prompt 的优先级规则（「涉及数据的事实必须来自工具」「无依据必须说明」）；
- **按角色/意图裁剪可选工具集**：我已有 `allowed_tool_names(role, tools)`，但**当前 loop 仍把 4 个全给模型** —— 这是一个明确的、低成本下一步；
- 前置便宜的意图分类（规则或小模型），把候选缩到 2–3 个再进 loop；
- 建评测集，把「工具选择正确率」变成指标，改 prompt 前后有回归。
`[PRODUCTION_NEXT]` 再加一层**后果分级**：只读工具选错，代价是一次多余查询，可以接受；**有副作用的工具选错，代价是一次错误操作**，所以副作用工具**不允许被模型自由选**——必须走人工确认（见 Q8-12）。

#### My Project Evidence

- `app/agent/executor.py`（UNKNOWN_TOOL / PERMISSION_DENIED / INVALID_ARGUMENTS）
- `app/agent/tools/business.py`（INVALID_OPERATION）
- `app/auth/permissions.py::allowed_tool_names`（已实现，**loop 未使用** → §22）
- `tests/unit/test_agent_permissions.py::test_invalid_arguments_are_reported_structurally`、`tests/unit/test_permissions.py::test_allowed_tool_names_per_role`

#### Follow-up Questions

- 你怎么发现选错工具？（审计里有 `user_input` 摘要 + tool 序列，可以统计异常组合；更正式的是评测集上的选择正确率）
- 让模型解释「为什么选这个工具」有用吗？（对**排障**有用，对**正确性**无保证。我会把它记进 trace，但不当成控制手段）
- 多次选错要不要自动升级到人？（要，且这是我在安全场景的默认姿态：连续无进展 → 停止 + 提示人工路径）

#### Pitfalls

- 不要说「prompt 写好就不会选错」。要把「已做的硬边界」和「只能靠概率改善的部分」分开讲。
- 不要把 `allowed_tool_names` 说成已在 loop 里生效——它现在是权限/UI 辅助函数。这个细节被追问到时说错，代价很大。

#### Interview Keywords

`three hard guards` `legal-but-wrong is probabilistic` `prune the tool set` `side-effect tools need HITL`

---

## Q8-12 如何做 Human-in-the-loop？

#### Short Answer

不是「加个确认按钮」，而是四件事：动作分级；Agent 只产出「待批准的建议」；人批准后由确定性流程执行；全过程留痕，且「建议」和「执行」是两个不同身份的事。

#### Standard Answer

`[MY DESIGN]` **我在 Demo 里做到的**：AI 的全部能力面就是 4 个**只读**工具，因此不存在需要审批的副作用——这是刻意的范围控制（`[FACT]` SPEC 0.1 第 7 条：本期只做分析/辅助决策）。但**边界的形状已经搭出来了**：`Tool.permission` + `ToolExecutor` 的检查点 + `tool.call` 审计行，这三处正好是插入审批的位置。
`[PRODUCTION_NEXT]` 完整设计（我会明确标注这是方案不是既成事实）：
```text
Agent → tool_call(write, risk=high)
      → executor 判定：该工具需要 approval → 不执行
      → 生成 ApprovalRequest{actor, request_id, tool, validated_args 快照,
                             依据的引用与数据快照, 过期时间}
      → 落库 + 通知审批人（审批人 ≠ 发起人；角色必须含该工具的审批权限）
      → 人在 Web 上看到「将要执行什么 + 依据是什么」→ 批准/驳回（带理由）
      → 批准后服务端用**存储的那份参数**重新校验（权限/幂等/数据是否已变）后执行
      → 审计两条：agent.proposal(...) 与 tool.execution(approved_by, request_id)
```
五个关键点：
① **风险写进工具定义**（`risk=low|high`、`reversible=bool`、`requires_second_party=bool`）——审批需求是**工具属性**，不是配置文件里的字符串；
② **参数快照**：批准后执行的是**人当时看到的那份参数**，不能重算。否则「批准的是 A、执行的是 B」；
③ **超时过期**：不批准就**不执行**，绝不自动通过；
④ **审批本身可追责**：谁批的、依据什么、什么时候——这是企业里唯一能撑起「AI 参与了决策」这件事的记录；
⑤ **降级路径**：审批人不可用时宁可失败。
`[INFERENCE]` 化工场景具体化：`[FACT]` 公开资料显示公司以安全环保为经营底线并推进「工业互联网 + 危化安全生产」相关建设（来源见 §来源）。`[INFERENCE]` 所以「人是最终决定者」应当是平台默认而不是选项。我的做法是：**AI 给的建议永远带制度引用 + 版本 + 有效期 + 一个留给责任人填写的字段**，且写操作一律走上面的审批流。
`[FACT]` **我会坚持不进入 Agent 能力面的动作清单**：联锁旁路、报警抑制、工艺参数修改、危险区域作业授权、人员进出许可。这些不是「需要审批」，是「不由 AI 平台提出」。

#### My Project Evidence

- `app/agent/tools/base.py::Tool.permission`（风险属性可以直接扩在这里）
- `app/agent/executor.py`（唯一插入点；检查发生在数据访问之前）
- `app/observability/audit.py::AuditStatus`（已有 `denied`，可扩 `pending_approval/approved`）
- `[FACT]` `SPEC.md` §0.1 第 7 条（本期禁止控制类动作）

#### Follow-up Questions

- 审批疲劳怎么办？（分级：低风险自动执行只留痕，高风险才打断人；把「自动通过率」与「人审批驳回率」做成运营指标来调阈值）
- 人批准了但结果错了，责任链是什么？（工程答案：全链留痕 + 参数快照可复核 + 依据引用可回查；组织答案要由平台使用规范写清，对应 JD 第 6 条）
- 如果 Agent 建议「什么都不做」，要不要审批？（要记录，不一定要审批——但「未采纳的建议」在事故复盘里往往最关键）

#### Pitfalls

- **不要说「我们支持人工确认」**——Demo 里没有任何写操作，也就没有审批。要说「我留有那个插入点，方案是这样」。
- 不要把 HITL 讲成 UI 特性：它是权限模型 + 工作流 + 审计三件事的交点。
- 不要把「AI 不做控制」说成保守——它是**能让整个平台被批准上线**的前提。

#### Interview Keywords

`proposal vs execution` `parameter snapshot` `risk as tool attribute` `never auto-approve on timeout` `excluded capability list`

---


# 9 · Tool Calling / Enterprise Integration

## Q9-01 Agent 怎么连接 ERP？

#### Short Answer

标准链路：Agent → 白名单 Tool（固定 operation + 参数化查询）→ 数据访问层 / ERP 只读 API → 结构化结果 → 双视图（给模型读的文本块 + 给平台用的 payload）。

#### Standard Answer

`[MY DESIGN]` 我项目里的具体链路：
```text
AgentRuntime
  → ToolExecutor（白名单 → 权限 tool:erp → Pydantic 校验 operation/days/limit/material/status/category）
  → ErpPurchaseAnalysisTool（7 个固定 operation → app/db/queries.py 对应函数）
  → SQLAlchemy text(sql) + 命名参数绑定 → SQLite（合成 ERP：suppliers/materials/purchase_orders/inventory）
  → ToolResult{content="【ERP 采购数据】… 1. 物料=原盐, 均价=…",
               metadata.payload={operation, days, row_count, data[], data_source, disclaimer}}
  → 回填成 tool 消息 → 模型解释结果 → 最终回答
```
三个我认为重要的设计决定：
① **双视图输出**：`content` 给模型（中文标签、最多 `MAX_CONTENT_ROWS=8` 行、明确标注「合成演示数据，非真实企业数据」）；`payload` 给平台（**SQL 列名保留**，前端/看板可程序化绑列）。让模型读全表既贵又容易抄错数字。
② **能力收敛成 operation**：模型只能从 `purchase_price_trend / top_materials_by_spend / supplier_summary / recent_purchase_orders / inventory_summary / material_consumption / purchase_amount_stats` 里选一个，别的什么都表达不了。
③ **口径与免责随数据走**：payload 里 `data_source="data/synthetic"` 与 `disclaimer` 是**和数据同一份对象**，不可能被「忘记标注」。
**接真实 ERP 时的差别**（`[PRODUCTION_NEXT]`，见 Q9-06）：把 `app/db/queries.py` 那一层换成 ERP 只读 API 适配器，**operation 契约不变**——Agent 侧、权限侧、审计侧一行都不用改。这是我这套设计最有价值的地方。

#### My Project Evidence

- `app/agent/tools/erp.py`（`Literal` operation + args_model + 7 个 operation → 查询函数映射）
- `app/agent/tools/business.py`（`BusinessQueryTool` 基类、`render`、`MAX_CONTENT_ROWS=8`、payload/disclaimer）
- `app/db/queries.py`（固定 SQL 常量 + 命名参数 + `BusinessQueryError`）
- `data/synthetic/{schema.sql,seed.json,README.md}`（8 供应商 / 10 物料 / ~328 采购订单 / 9 库存 / 6 设备 / 6 维修记录）
- `tests/unit/test_erp_tool.py`（26）、`DEMO_SCRIPT.md` Step 4

#### Follow-up Questions

- 真实 ERP 表结构和口径与你的假设不一致怎么办？（先做映射层 + 与业务确认字段 owner，再谈 Agent）
- 数据量大了怎么办？（limit + 预聚合视图 + 分页；绝不允许全表扫）
- 权限粒度到单据级吗？（`[PRODUCTION_NEXT]` 需要 ERP 侧角色映射，不由 AI 平台自造）

#### Pitfalls

- **当前是合成 ERP，绝对不要说「我接过 ERP」**。被追问「你们 ERP 是什么系统」时用 §23 Q23-03 的标准答法。
- 不要说「AI 平台里存一份 ERP 数据副本」——那是数据主权的错误做法（见 Q9-06）。

#### Interview Keywords

`fixed operation` `dual view output` `parameter binding` `swap adapter not contract`

---

## Q9-02 为什么不能让 LLM 随便生成 SQL？

#### Short Answer

因为自然语言里的意图没有权限概念。让模型生成 SQL 等于把「谁能读什么」交给一个概率模型判断，而且一条语句就能扫全库、拖慢库、读到不该读的列。

#### Standard Answer

具体风险（按严重度）：
① **权限绕过**：`SELECT * FROM payroll` 语法完全合法。SQL 层没有「这个角色不该看这张表」的语义，除非你在 DB 层做角色—表/列授权，那是另一个独立得多的系统；
② **数据泄露进模型上下文**：读出来的内容进 prompt，然后可能被答案引用出来。我的审计不记 prompt 正文，但**答案会带出内容**；
③ **资源失控**：一个无 WHERE 的 JOIN 能把只读库拖死，并连带把整条 Agent 链路挂住；
④ **不可测试**：模型生成的 SQL 每次不同，我无法为它写回归测试，也无法证明它「不会」做什么；
⑤ **口径错误更隐蔽**：SQL 写错了照样出数——少一个 `GROUP BY` 也能跑通。错误从「格式错」变成「数字看着对但错」，这是最危险的一类。
`[MY DESIGN]` 我的替代方案：**固定 operation + 参数绑定 + Pydantic 范围校验 + limit**。所以模型能表达的是「按采购金额排名前 10、看 30 天窗口、物料过滤=盐酸」，**不能表达的是「任何别的」**。
一个必须正面回答的反驳：「Text2SQL 很灵活，业务方想问什么都能问」。我的答案是：**灵活性靠增加 operation 来给**——每个 operation 都是一次带评审的变更（写 SQL、定权限、加测试、确认口径 owner），而不是把自由文本变成可执行代码。企业里「新加一个查询」应该是周级流程，不是运行时行为。
`[PRODUCTION_NEXT]` 真需要 ad-hoc 分析时的正确做法：给一个**语义层/预授权只读视图集**（行列级权限在 DB 或 BI 层强制），让模型只能在这个视图集上生成 SQL，并强制 `LIMIT` + 只读事务 + statement timeout + **把 SQL 原文显示给人看**。即便如此我仍把它列为第二阶段以后的事。

#### My Project Evidence

- `app/db/queries.py`（每段 SQL 是模块级常量 `_*_SQL`，只通过 `text(sql)` + `params` 执行；`WHERE po.order_date >= :cutoff`、`LIMIT :limit`、`(:material IS NULL OR m.name LIKE :material_like)`）
- `app/agent/tools/erp.py`（`Literal` 枚举 = 能力面）
- `app/agent/executor.py`（`INVALID_ARGUMENTS` 在任何执行之前）
- `tests/unit/test_erp_tool.py`（非法 operation / 越界参数被拒）
- `[FACT]` `SPEC.md` §0.1 第 4、5 条（本期禁止任意 SQL / 必须参数化）

#### Follow-up Questions

- 参数化能防注入，那它能防越权吗？（**不能**。SQL 注入和越权是两类问题：前者靠参数绑定，后者靠权限模型。混着说是外行）
- DBA 只肯给一个通用查询视图，你怎么加边界？（列白名单 + 强制 LIMIT + 只读账号 + statement timeout + 审计）
- 只读账号该配什么限制？（独立账号、statement timeout、行数上限、schema 白名单、连接数上限、单独审计）

#### Pitfalls

- 不要把「SQL 注入」和「越权」混着说。
- 不要说「模型不会写坏 SQL」。

#### Interview Keywords

`intent ≠ authority` `operation not expression` `SQL injection ≠ privilege escalation` `semantic layer for ad-hoc`

---

## Q9-03 如何控制 Tool 权限？

#### Short Answer

工具权限是**独立一族**权限（`tool:*`），由 `ToolExecutor` 在数据访问**之前**强制；路由权限不会传递给工具，前端隐藏也不算数。

#### Standard Answer

`[MY DESIGN]` 三层控制（详见 Q5-06）：
① **能力面**：`ToolRegistry` 只注册显式登记的工具，未登记 = `UNKNOWN_TOOL`，不执行；
② **权限**：`Tool.permission`（`tool:knowledge` / `tool:erp` / `tool:safety`），由 `ToolExecutor` 用 `has_permission(actor.role, ...)` 判；**未认证即拒（fail-closed）**，记 `PERMISSION_DENIED` + 审计 `denied` + `permission_denied_count`；
③ **参数与 operation**：Pydantic 校验 + 业务工具内部的 operation 白名单再各查一次。
三个企业集成语境下一定会被追问的点：
- **粒度还能更细**：我现在是「工具粒度」，更细的有两个维度——**operation 粒度**（`supplier_summary` 与 `recent_purchase_orders` 敏感度不同，不该同权）和**数据范围粒度**（同一 operation，A 基地只能看自己）。扩展形状很直接：`Tool.permission` 从单个值换成集合，executor 改成 `any(...)`；数据范围则复用 Q7-14 的 metadata ACL。
- **默认值有争议**：`Tool.permission` 目前有默认值（能跑 Agent 就能用），业务工具都显式覆盖了。`[PRODUCTION_NEXT]` 我会把默认改成**必须显式声明，否则不注册**——安全属性不该有默认值。
- **权限变更要立刻生效**：权限判定走内存矩阵（每次请求实时读，无缓存），生产上如果引入缓存就必须给失效通道。
④ **不要在前端做**：Web Console 的角色切换只换 Authorization header，后端仍按 token 判角色。`tests/integration/test_web_console_contract.py::test_models_is_403_for_operator` 就是钉这一点的。

#### My Project Evidence

- `app/auth/permissions.py`（模块文档写明两族权限互不继承 + `_TOOL_PERMISSIONS` 映射）
- `app/agent/executor.py`（检查发生在 `tool.execute` 之前）
- `app/observability/audit.py::record_tool_call`（每次调用一行，含被拒的）
- `tests/unit/test_permissions.py`（矩阵/映射/role 判定）、`tests/unit/test_agent_tools.py`

#### Follow-up Questions

- 被拒的工具要不要从模型的可见列表里剔除？（应该要，见 Q8-11 的 `allowed_tool_names` 未接入 loop）
- 一个工具有多个 operation，权限该配在哪一层？（operation 层；工具层只解决「能不能进这个门」）
- 服务账号（Agent 自己）要不要有权限？（不要。它只能代表某个 `Actor` 行事，永远不拥有独立授权——这是防「Agent 提权」的关键设计）

#### Pitfalls

- 不要说「executor 检查一次就够」。路由层与执行层是两条独立入口（直接 API 调用 vs 模型在 loop 里请求），必须两处都有。
- 不要说「工具权限和路由权限是一个东西」。我在模块文档里专门把它们分成两族，就是为了不让「能调 /api/agent/run」自动等于「能查 ERP」。

#### Interview Keywords

`two permission families` `fail-closed` `check before data access` `operation-level granularity next`

---

## Q9-04 Tool timeout 怎么处理？

#### Short Answer

现在**没有** per-tool timeout，这是真实缺口。生产上必须有，而且 timeout 之后必须区分「确定未执行」和「可能已执行」。

#### Standard Answer

`[MY DESIGN]` 现状：工具是 `await tool.execute(arguments)`，没有超时包装，只有 try/except。所以一个慢查询会一直占着这条 Agent 链路（HTTP 侧只有 nginx 的 `proxy_read_timeout 120s` 和 provider 的 `timeout=60.0`，都**不是工具级**）。我会主动承认这一点，然后说清怎么修。
`[PRODUCTION_NEXT]` 设计五条：
① **timeout 是工具属性**（低延迟查询 2s、ERP 只读 API 5s、外部 HTTP 10s），超时 → `ToolResult(success=false, error_code="TIMEOUT")` + 审计 error 行 + 指标计数；
② **取消必须真的传下去**：httpx 有 request timeout；SQLAlchemy 需要 `statement_timeout` 或驱动级选项。**否则「超时」只是我不看了，DB 还在跑**——那是最坏情况：资源没释放，还多了一份假故障；
③ **副作用语义**：只读工具超时 = 可安全重试候选；**写操作超时 = 未知状态**，必须幂等键 + 对账（Q9-05），绝不自动重试；
④ **预算不等式**：工具 timeout 之和 ≤ Agent 墙钟 deadline ≤ HTTP 侧超时。当前我只有步数预算，**没有这个不等式**，这是我要补的第二件事；
⑤ **降级呈现**：某工具连续超时 → 熔断（暂时不放进可选工具集）或返回带时间戳的缓存快照并明确标注，而不是让每个用户都撞一次。

#### My Project Evidence

- `app/agent/executor.py`（无 timeout，只有 try/except → 缺口本身是证据）
- `app/gateway/openai_compatible.py`（provider 侧有 `timeout=60.0`，说明我知道该在哪配）
- `web/nginx.conf`（`proxy_read_timeout 120s`）
- 缺口记录：§22

#### Follow-up Questions

- 数据库查询超时怎么**真正**取消？（驱动/服务端：`statement_timeout`、连接池回收、或把查询放进可取消的独立连接——不是 Python 侧 `asyncio.wait_for` 就完事）
- 超时该给用户看什么？（「本次未能取得 X 数据」+ 已获得的引用，而不是一个假装完整的回答）
- 你设多久？依据什么？（下游 P99 + SLA，不是拍脑袋。而我还没有下游数据 → 所以先埋点）

#### Pitfalls

- **不要说「我有超时」——没有。** 这是最容易被戳穿的一处，先自曝。
- 不要说「async 自动给你超时」。异步只给你并发，不给你截止时间。

#### Interview Keywords

`per-tool deadline` `cancel propagation` `unknown state on write timeout` `budget inequality`

---

## Q9-05 Tool 幂等性怎么处理？

#### Short Answer

读操作天然幂等，写操作必须带幂等键；原则是「谁发起重试，谁携带同一个键」，且幂等窗口必须大于最长故障恢复时间。

#### Standard Answer

`[MY DESIGN]` 我这个 Demo 的 4 个工具全只读，所以幂等性问题不存在——这一点我说清楚，而不是假装解决了一个没出现的问题。
但我**有**一个真实做过的幂等案例：**ingest**。`rebuild=True` 是幂等的（清空重灌，同目录跑两次结果一致）；默认模式下按 `document_id` upsert，跑两次不会翻倍。另外数据播种层的幂等我是**测过的**：`tests/unit/test_database.py::test_re_running_seed_does_not_duplicate_rows`、`test_force_reseed_rebuilds_the_same_data`。
`[PRODUCTION_NEXT]` 企业写操作的方案：
① **幂等键由调用方生成**（`Idempotency-Key` 或业务单号），平台把它作为去重主键存下来；同 key 重复请求返回**第一次的结果**（**包括失败结果**），而不是重新执行；
② **存储**：key → {请求哈希、状态、结果}，保留期 > 最大重试窗口；
③ **同 key 不同参数 = 客户端 bug** → 409 `CONFLICT`，绝不静默执行新的（这个分支最容易被漏，也最能区分「做过分布式写」和「听说过幂等」）；
④ **Agent 侧落点**：`ToolCall.id` 可作为键来源之一，但更稳的是业务级去重（`request_id + operation + 参数哈希`），因为 provider 的 call id 不保证跨重试稳定；
⑤ **超时后未知状态**：靠对账查询下游是否已存在该单据，而不是重试；
⑥ **审批流同样要幂等**：审批人连点两次不能生成两张单。

#### My Project Evidence

- `app/rag/ingest.py`（`rebuild` / upsert 语义 + `IngestReport`）
- `tests/unit/test_database.py`（两条幂等测试，可当场指出）
- `app/gateway/base.py::ToolCall.id`（潜在幂等键来源 + 它为什么不够稳）
- `app/api/errors.py`（已有 `CONFLICT` 409 语义可复用）

#### Follow-up Questions

- 幂等窗口设多久？谁定？（≥ 客户端最大重试跨度 + 人工排障时间；由集成协议双方共同定）
- 下游 ERP 不支持幂等怎么办？（我这边「一次执行 + 记录」，并在集成协议里要求它提供查询接口用于对账）
- 幂等键存哪儿、跟谁的 TTL？（独立于业务表的短生命周期 KV；生产上要共享存储 → 又是 Redis 的第一个真实理由）

#### Pitfalls

- 不要说「我们所有工具都幂等」——只有只读工具天然幂等。
- 不要漏「同 key 不同参数」分支。

#### Interview Keywords

`read-only idempotent by default` `client-generated key` `same key different args = 409` `reconcile not retry`

---

## Q9-06 真实 ERP 接进来第一步怎么做？

#### Short Answer

不是写代码，是把三件事谈清楚：**数据主权**（谁是 owner、AI 平台不落业务数据副本）、**只读通道**（预授权视图 + 限流）、**口径责任人**（数字算错了谁负责）。之后才做第一个 operation。

#### Standard Answer

我给自己排的前 8 周（明确不含任何「我猜公司有什么系统」）：
**第 1–2 周｜边界与事实**
- 摸清现有哪些系统（`[FACT]` JD 只写了「ERP、OA 等」`[INFERENCE]` → 具体清单需入职后核实）、谁维护、有无只读账号、有无 API、变更窗口；
`[需要本人确认：入职后可获得的跨部门协作授权范围]`
- 定三条不可谈判的边界：**第一期 AI 平台不写业务系统**；**不长期存业务数据副本**（避免第二套真相 + 新增泄露面）；**任何对生产/安全有后果的动作不进入 Agent 能力面**；
- 选一个**低敏感、可当场验证**的场景起步：我倾向供应商/采购分析（只读、口径业务方能一眼验、不含人员数据）。
**第 3–5 周｜最小只读通道**
- 申请只读账号/预授权视图（行列级权限、statement timeout、独立 DB 用户、连接数上限；**视图定义由 ERP owner 签认**）；
- 只做**一个** operation，并把它的口径写成测试（例如 `top_materials_by_spend` 与业务报表同窗口同数字）；
- 权限沿用现有形状（`tool:erp` + 角色矩阵 + executor 检查 + `tool.call` 审计），不新造概念；
- 数据不落本地：响应直连模型上下文。**若为性能要缓存，缓存 key 必须含 principal + 权限集**，且有 TTL 与主动失效——否则缓存就是一个越权读取通道。
**第 6–8 周｜可观测与试点**
- 每个 operation 的调用量、P95、失败率进指标；每次调用进审计；
- 找 2–3 个真实用户（采购/财务）试用两周，只收集三件事：数字对不对、口径对不对、引用能不能核对；
- 输出一份平台使用规范：谁能看什么、「答案不可直接作为决策依据」的条款、异常上报路径（对应 `[FACT]` JD 第 6 条）。
**技术形状**（我认为这套 Demo 最可迁移的部分）：`[MY DESIGN]` 换的是 `app/db/queries.py` 底下那一层——从 SQLite 换成 ERP 只读 API 适配器；**operation 契约、Pydantic 参数、executor 权限检查、审计与双视图输出全部不变**。这就是我为什么把工具设计成 operation 白名单而不是 SQL 字符串：**接真实系统时改的是适配器，不是安全模型。**

#### My Project Evidence

- `app/db/queries.py` + `app/agent/tools/erp.py`（适配层形状）
- `app/services/agent_service.py`（依赖注入：工具的 database 可替换 → 测试与真实接入共用同一构造函数）
- `app/agent/tools/business.py::payload.data_source`（数据来源随数据走）
- `app/observability/audit.py::record_tool_call`（每次调用一行，含被拒）

#### Follow-up Questions

- ERP 团队说「不给视图，只能用他们的标准 API，一次只能查一张单」怎么办？（N+1 有预算 + 预聚合策略 + 与他们对齐批量接口，并把限流写进工具 timeout；**不擅自同步数据到自己库里**）
- 数字和 ERP 报表不一致，业务方先信谁？（先建对账测试 + 口径文档化 + 引用报表编号。这是产品问题不只是技术问题，我会把它提到规范里）
- 第一步最想接的**不是** ERP 的是什么？（制度/SOP 知识库：风险最低、见效最快、不需要业务系统任何写权限）

#### Pitfalls

- 不要给「两周接入全量 ERP」的承诺。**范围承诺是最快失去信任的方式。**
- 不要说「我们把 ERP 数据同步到我们库里」——企业里通常被直接否决（双份真相 + 数据分级失控）。
- **不要编造对恒光现有系统的任何了解**。`[INFERENCE]` 只用 JD 的措辞（`[FACT]` 第 3 条「对接企业内部 ERP、OA 等系统」）与公开资料里能看到的信息化/智能工厂方向做推演。

#### Interview Keywords

`data sovereignty first` `pre-authorized read-only views` `one operation end to end` `adapter swap keeps the contract` `cache key includes principal`
# 10 · MCP

> 本节涉及的外部事实均来自 MCP 官方规范站点，检索时间 **2026-10-01**（见 §来源）。
> MCP 规范迭代很快，我在面试里会先说「我读到的是哪个版本」，不背版本号当常识。

## Q10-01 什么是 MCP？

#### Short Answer

Model Context Protocol：一个基于 JSON-RPC 2.0 的开放协议，标准化「应用如何把工具、数据、提示模板暴露给 LLM 应用」。它的类比对象是 LSP——不是让模型更聪明，而是让宿主应用与外部能力之间有通用接口。

#### Standard Answer

`[FACT]`（MCP 规范，2026-10-01 读取）MCP 用 JSON-RPC 2.0 在三种角色之间通信：**Host**（发起连接的 LLM 应用）、**Client**（宿主内部的连接器）、**Server**（提供上下文与能力的服务）。Server 可以向 Client 提供三类特性：**Resources**（供用户或模型使用的上下文与数据）、**Prompts**（面向用户的模板消息与工作流）、**Tools**（供模型执行的函数）；Client 也可以向 Server 提供 **Elicitation**（服务端主动向用户追问补充信息）。协议另有可选扩展（例如 Tasks：长任务的异步执行）。规范明确把「工具代表任意代码执行，必须谨慎对待；宿主在调用任何工具前必须获得用户明确同意；工具描述本身应视为不可信输入」列为安全原则。
`[MY DESIGN] 理解层：` 对我这个岗位最有用的一句话：**MCP 标准化的是「接入形状」，不是「治理」**。权限、审计、数据边界、成本控制这些仍然得由平台自己实现——规范自己也这么承认（它说协议本身无法在协议层强制这些安全原则）。

#### Follow-up Questions

- 你说你了解 MCP，那 Client 和 Host 的边界具体在哪？
- 它和 function calling 的关系你再说一遍（见 Q10-02）。
- 规范最近有哪些变化你会关心？（我不会引用我不确定的条目；我知道它按日期版本迭代，落地前我会去读当时的正式规范）

#### Pitfalls

- 不要说「MCP 就是工具调用的标准」。它还包括 Resources 与 Prompts，且是「客户端—服务器」协议。
- 不要说「MCP 提供鉴权/安全」。规范定义了 HTTP 场景下的授权框架，但它明确说自己不能在协议层强制安全原则。
- 不要装读过全部规范。承认「我读过 overview 与 server 侧三个特性的部分章节」更可信。

#### Interview Keywords

`JSON-RPC` `Host/Client/Server` `Tools/Resources/Prompts` `governance is still yours`

---

## Q10-02 MCP 和普通 Tool 有什么关系？

#### Short Answer

function calling 回答的是「模型怎么表达一次工具请求」；MCP 回答的是「工具从哪儿来、谁提供、宿主怎么发现和调用它」。一个是模型接口，一个是分发协议。

#### Standard Answer

| 维度 | 我的 Tool（function calling） | MCP Tool |
|---|---|---|
| 定义在哪 | 我的进程内，代码里注册 | 外部进程/服务，通过协议发现 |
| schema 来源 | `Tool.args_model` → `to_openai_schema()` | Server 声明，Client 拉取 |
| 谁执行 | 我的 `ToolExecutor` | 远端 Server 执行，结果回传 |
| 信任边界 | 全在我进程内 | 跨信任边界：Server 的描述与返回都是外部输入 |
| 权限 | `Tool.permission` + executor 强制 | 平台自己强制（协议不替你决定谁能用） |
`[MY DESIGN] 理解层：` 所以我的判断是：**MCP 是 function calling 的「跨进程分发层」**。接入形态变了，但平台必须做的那四件事一件都不能少——白名单（不能因为 server 能发现就自动放行）、参数校验（server 的 schema 是不可信输入，仍需在我方边界二次校验）、权限（把调用方身份映射到 server 侧身份，而不是共享一个大账号）、审计（每次 MCP 调用也要一行留痕）。
一句话：**MCP 让你少写胶水，不让你的信任边界变松。**

#### My Project Evidence

- `[MY DESIGN]` `app/agent/tools/base.py::to_openai_schema()` 是我把 schema 单一来源化的地方——这个形状天然可序列化成 MCP 的 tool 声明
- `[MY DESIGN]` `app/agent/executor.py` 的「白名单 → 权限 → 校验 → 执行」顺序，正好是 MCP client 侧需要补的治理层

#### Follow-up Questions

- MCP Resource 和 RAG 检索是什么关系？（Resource 是「可列举可读取的上下文来源」；我的 knowledge_search 目前是 Tool。哪个当 Resource 取决于我是要「模型主动拉」还是「用户可选择挂载」）
- MCP 的 Prompts 特性你会用吗？（平台侧 prompt 版本管理是一个真实需求，但企业策略型 prompt 我更愿意自己管）
- 用 MCP 之后还需要自建 registry 吗？（需要，registry 变成「信任与治理的登记处」，不只是名字映射）

#### Pitfalls

- 不要说「MCP 会取代 function calling」，规范里 Tools 就是提供给模型执行的函数，两者是嵌套关系。
- 不要说「用了 MCP 就自动能跨模型复用」——复用来自协议标准化，仍然需要宿主支持 MCP。

#### Interview Keywords

`distribution layer` `schema is untrusted input` `identity mapping` `whitelist still required`

---

## Q10-03 为什么企业平台可能使用 MCP？

#### Short Answer

因为企业内部会有多个 AI 前端（IDE、聊天台、业务系统内嵌助手）和多个能力提供方（ERP、OA、文档系统、数据平台），M×N 的胶水会变成维护黑洞；MCP 把这件事变成 M+N。

#### Standard Answer

`[INFERENCE]` 恒光这个岗位的现实约束（基于 JD 公开条目推演，**不是公司事实**）：一个人建平台、要接的内部系统会随时间增多（JD 第 3 条写 ERP、OA，且带「等」），同时会有多个部门想用同一个能力。这种结构下最怕的是「每个系统各写一套私有集成」，三年后没人能维护。
MCP 能带来的三件具体好处：
① **能力提供方与消费方解耦**：ERP 团队按协议发布一个 server，我这边任何 Agent/前端都能接；他们升级接口不破坏我的代码（前提是 schema 协商正常）；
② **复用与生态**：`[FACT]` JD 第 2 条列的 Dify/RAGFlow/FastGPT/one-api/new-api/MCP 属于同一生态位——如果这些组件都开始讲 MCP，我的平台可以既当 server 又当 client，把「公司能力目录」变成一份可被任何支持 MCP 的应用消费的清单；
③ **审计点集中**：所有跨系统调用都经过我的 client，等于我天然拿到一个统一出口做留痕、限流、身份映射。
它解决不了的（也是我要主动说的）：企业内部权限模型、数据分级、审批流、成本归因——协议不提供，平台必须自己实现。规范自己也这么写。

#### Follow-up Questions

- 如果公司内只有一个 AI 前端，MCP 还值吗？（不值，我会用进程内工具，见 Q10-05）
- 你会用现成 MCP server 还是自己写？（现成的先看它的认证与数据流向；对 ERP 这类核心系统我一定自己包一层受控 server）
- 怎么防止 server 泛滥没人维护？（registry 化 + owner 制 + 定期体检）

#### Pitfalls

- 不要把「用 MCP」说成先进性的证明。要给出规模判据：≥2 个消费端 且 ≥3 个能力端，我才认真评估。
- 不要承诺「MCP 能提升安全性」——它提升的是互操作，安全是新增加的攻击面（第三方 server 的描述与返回都是外部输入）。

#### Interview Keywords

`M+N not M×N` `capability catalog` `unified egress for audit` `new untrusted input surface`

---

## Q10-04 MCP Server / Client / Tool / Resource 是什么？

#### Short Answer

Host 是 LLM 应用；Client 是宿主里与某个 server 一对一的连接器；Server 提供 Tools（模型可执行）、Resources（可读取的上下文数据）、Prompts（面向用户的模板）。

#### Standard Answer

`[FACT]`（规范 overview，2026-10-01）
- **Host**：发起连接的 LLM 应用（IDE、聊天界面、我的平台服务）；
- **Client**：宿主内部的连接器，一个 client 通常对应一个 server 连接，负责能力协商与消息转发；
- **Server**：提供上下文与能力的服务；
- Server 侧三类特性：**Tools**（模型可调用执行的函数）/ **Resources**（供用户或模型使用的上下文与数据）/ **Prompts**（模板消息与工作流）；Client 侧可提供 **Elicitation**（server 主动向用户追问）。
`[MY DESIGN] 理解层：` 我特别在意 **Tools 与 Resources 的分工**：Tool 是「模型主动要一个动作」，Resource 是「可被列举、可被读取的一份上下文」。映射到企业场景：制度文档清单/目录天然是 Resource（可枚举、有 URI），而「按 base + 时间窗统计安全事件」是 Tool（有参数、有执行、有副作用风险）。我现在把 knowledge_search 做成 Tool，是简化选择（避免在 Demo 里同时实现两类），不是我认为它只能是 Tool。
另外我会记住规范的安全表述：**工具描述这类元数据在来自可信 server 之前应视为不可信**（`[FACT]`）。这直接影响我的设计：如果引入外部 MCP server，它的 tool description **不能**原样进模型 prompt，需要经过我方登记与审校——否则就是间接 prompt injection 的入口。

#### My Project Evidence

- `[MY DESIGN]` 对照我的实现：`ToolRegistry` ≈ server 的 tool 列表；`openai_schemas()` ≈ `tools/list`；`ToolExecutor.execute()` ≈ `tools/call`；`Actor`（身份+request_id）≈ client 侧应透传的调用主体
- `[MY DESIGN]` `app/rag/` 的 documents 列表接口（`GET /api/knowledge/documents`）形状上就是一个 Resource 目录

#### Follow-up Questions

- sampling（server 反过来请求宿主调模型）你知道吗？（不确定当前版本条目，我会去查，不猜）
- Resources 变更通知你怎么处理？（协议有订阅/通知模式，我的答案是要落到「索引重建触发」而不是「实时读」）
- 一个 server 里 tools 太多怎么办？（分组/分层，或按角色暴露不同 tool 集——这正好接回我的 `allowed_tool_names`）

#### Pitfalls

- 不要把四个概念讲串（常见错误：把 Resource 说成「知识库」，把 Client 说成「前端」）。
- 不要说「MCP 有标准权限模型」。

#### Interview Keywords

`tools/list + tools/call` `resource = enumerable context` `untrusted descriptions`

---

## Q10-05 当前项目为什么没有强制使用 MCP？

#### Short Answer

因为我现在只有 1 个消费端（我自己的 Agent）和 4 个同进程工具。MCP 的收益要跨进程、跨应用才出现，成本（协议实现、发现、协商、序列化）立刻就要付。

#### Standard Answer

`[MY DESIGN]` 三个理由：
① **同进程调用不该网络化**：`knowledge_search` 直接持有 `KnowledgeService` 实例，走 JSON-RPC 只会多一次序列化、多一个失败模式、多一层需要处理的取消与超时（而超时我本来还没做）；
② **本期目标是先证明核心 Agent workflow 成立**：SPEC 0.1 明确「先做最小闭环，禁止过度工程化」，并把 K8s/Kafka/Redis/微服务列为本期禁止扩张项。MCP 不在 SPEC 的禁止清单里，但它属于同一类判断：在只有一个宿主时，它不解决我的问题；
③ **我不引入我不能解释每一行的东西**：面试里我要能回答「为什么权限检查在这个位置」。协议实现会把我带到「这层行为由 SDK 决定」上。
同时我做了**为 MCP 留门的准备**：工具定义是声明式的（name/description/args_model/permission 四件套 + 从 Pydantic 生成 schema），执行入口是单一的（`ToolExecutor`），身份是显式传递的（`Actor`）。这意味着我实现一个 MCP server 只需要把 `registry.openai_schemas()` 换成 `tools/list` 响应、把 `executor.execute(call, actor)` 包成 `tools/call` handler——**契约不变，只是把边界外移一层**。这是我真正想表达的点：我不用 MCP，但我的抽象不会阻碍 MCP。
`[INFERENCE]` 对恒光：`[FACT]` JD 把 MCP 列在「持续研究开源 LLM 应用生态，评估并引入适合公司业务的技术方案」这一条里。所以这个岗位对 MCP 的要求我读成「能判断何时引入并落地它」，而不是「必须已经用过」。我按前者准备。

#### My Project Evidence

- `app/agent/tools/base.py`（声明式工具定义 + schema 单一来源）
- `app/agent/registry.py::openai_schemas`（协议映射点）
- `app/agent/executor.py::execute(call, actor=…)`（协议映射点）
- `SPEC.md` §0.1 第 2 条（禁止过度工程化）、§21（MCP tools 在 Phase 2）

#### Follow-up Questions

- 那你第一步 MCP 化会做什么？（见 Q10-06）
- 用现成 Python MCP SDK 还是自己实现协议？（优先官方 SDK，但先做 capability 与兼容性验证；我不写私有协议）
- 如果 ERP 团队已经有一个 MCP server，你还包一层吗？（包。我需要自己的权限、审计、限流、身份映射，那一层不能外包）

#### Pitfalls

- 不要说「MCP 没必要」，要说「在 1 个宿主 + 同进程 4 工具这个规模下收益不成立」。
- 不要显得抗拒：正确姿态是「我已经把接入点留在哪说清楚了，这是我会做的第一步」。

#### Interview Keywords

`single host no cross-process win` `declarative tool contract` `protocol mapping points ready`

---

## Q10-06 如果把 ERP 接口做成 MCP Server，怎么设计？

#### Short Answer

把「查询能力」留在 ERP 侧（只读视图 + 预授权），把「治理」留在平台侧（身份映射、权限、审计、限流、超时）。Server 只暴露固定 operation 的 tools，不暴露任何自由查询能力。

#### Standard Answer

我的设计（全部标 `[MY DESIGN]` / `[PRODUCTION_NEXT]`，这是一个方案不是既成事实）：

**1. 切分**
```text
AI 平台（Host）
  └─ MCP Client（一个连接一个 server）
        ├─ 身份映射：CurrentUser → ERP 侧只读账号/租户上下文（绝不共享大账号）
        ├─ 权限：tool 级 + operation 级（映射到我现有的 Permission 家族）
        ├─ 参数二次校验：不信 server 的 schema，在我方边界再验一遍
        ├─ 审计：每次 tools/call 一行（actor、request_id、tool、operation、status、latency）
        └─ 预算：per-call timeout + 平台侧限流 + 熔断
ERP MCP Server
  ├─ tools/list：固定 operation（价格趋势 / 采购额排名 / 供应商汇总 / 最近订单 / 库存 / 消耗 / 品类统计）
  ├─ 只读视图 + statement timeout + 行数上限
  └─ 不暴露：任意 SQL、表名参数、写操作（第一期）
```

**2. 工具契约**
每个 operation 一个 tool，name 稳定、description 经我方审校（因为规范要求把工具描述视为不可信输入 `[FACT]`）、inputSchema 由 ERP 侧提供但平台侧存一份「已核准版本」做**漂移检测**（server 悄悄改 schema → 平台报警并停用该 tool，而不是静默接受）。

**3. 分两类 Resource**
`erp://suppliers/{id}`、`erp://materials/{code}` 作为 Resource 供按需读取；聚合统计保持 Tool（有参数、有执行成本）。这样模型能「看一眼这条物料」，但拉不到「全库」。

**4. 写操作（第二期以后）**
必须走审批：Agent 只能产出 proposal；人批准后由**确定性流程**执行；幂等键 + 参数快照 + 执行前重新校验（见 Q8-12）。我会坚持：写操作的执行者不是模型选出来的，是流程调出来的。

**5. 迁移路径（我可以从当前代码怎么走）**
`ToolRegistry` 增加一个 `RemoteTool` 实现（`Tool` 协议的另一个实现者，name/description/args_model/permission 都齐）；`build_default_registry` 里把 ERP 工具的构造从「本地 queries」换成「MCP client + 已核准 schema」；`ToolExecutor` **不改**（权限/校验/审计/异常收口全部复用）；`AgentRuntime` **不改**。
这个「只加一个实现类、不动安全边界」的性质，就是我认为好的抽象该有的样子——也是我面试里最想展示的一句结论。

**6. 验收**
先影子运行（只记录不返回给用户，比对 ERP 报表口径）→ 单部门小流量 → 全量。每一步的判据：数字一致率、P95 延迟、`tool.call` 错误码分布。

#### Follow-up Questions

- server 不可用时平台怎么表现？（熔断 → 该 tool 不进可选集 → 回答明确标注「未取得业务数据」，而不是静默缺数据）
- 你怎么防「通过 operation 组合拖库」？（限流 + 单次行数上限 + 成本预算 + 慢查询熔断）
- 谁负责 server 的 schema 演进？（我提的漂移检测 + 版本化 tool 名，例如 `_v2` 并行期）

#### Pitfalls

- 不要设计成一个 `erp_query(sql)` 万能 tool——那等于把 §Q9-02 禁止的事换个协议重做一遍。
- 不要说「MCP server 就有鉴权了」。身份映射与授权是平台侧工作。
- 不要把这个方案说成「我做过的」，它是 `[PRODUCTION_NEXT]` 的设计提案。

#### Interview Keywords

`governance stays platform-side` `schema drift detection` `one new Tool impl, executor unchanged`

---

# 11 · 企业 AI Platform（标准系统设计题）

## Q11-01 「如果让你从 0 到 1 给恒光设计一个私有 AI 平台，你怎么做？」

> 这是本岗位最可能出现的系统设计题。下面是一份完整答案，我会按「需求澄清 → 架构 → 数据流 → 安全 → 失败处理 → 监控 → 扩展 → 分阶段落地」的顺序讲，控制在 6–8 分钟，中间在「第一阶段做什么」处主动停下来问面试官意见。

### Step 0 · 先问清楚（不问就画图是我最想避免的事）

1. **用户是谁**：机关（工艺/设备/安环/采购/财务/HR）还是车间一线？有没有移动端诉求？大致人数？
2. **数据边界**：是否必须完全内网？能否调用外部模型 API（哪怕脱敏后）？这条直接决定模型形态。
3. **第一批场景**：谁在痛？哪个场景的失败代价最低？（我会主动建议从知识库/RAG 起步，理由见下）
4. **身份与权限来源**：有没有 AD/LDAP/SSO？有没有既有的角色体系可复用？
5. **ERP/OA 的接入形态**：有 API 吗？DBA 能不能给只读视图？谁是数据 owner？
6. **合规与留存要求**：审计要不要不可篡改？留多久？谁有权看审计？
7. **运维半径**：几个人维护？有没有 GPU？谁批变更窗口？（`[FACT]` JD 显示这个岗位招 1 人 `[INFERENCE]` → 我会按「一人可维护」设计，并明确说出这个假设）

### Step 1 · 目标架构（一张图，能白板上画出来）

```text
用户（机关 PC / 车间终端 / 移动）
   │ HTTPS
Web 门户 + 内嵌助手          ← 同一套 API 契约，前端不持有特权
   │
API Gateway / 平台服务（FastAPI）
   ├─ 认证：SSO/JWT → 会话 → CurrentUser（平台不自建账号体系）
   ├─ 授权：角色 → 权限矩阵（路由权限 + 工具权限 两族，互不继承）
   ├─ 请求上下文：request_id 贯穿全链
   ├─ 限流/配额：按用户/部门/agent
   ▼
┌──────────────── 能力层 ────────────────┐
│  Model Gateway   │  RAG 服务   │ Agent Runtime │
│  多模型接入/路由  │ ingest/检索  │ 有限 loop     │
│  降级/成本/评测   │ ACL/引用     │ 工具白名单    │
│  （唯一模型出口） │（服务端强制） │（executor 边界）│
└────────────────────────────────────────┘
   │                     │                    │
推理服务（vLLM/Ollama）  向量索引 + 元数据库   Tool Adapter 层
embedding / rerank      对象存储（原件）      ├─ ERP 只读视图/API
                                            ├─ OA（流程/制度）
                                            ├─ 安全/隐患台账
                                            └─ 设备台账/维修记录
   │
横向：Audit（append-only，独立写账号）｜ Metrics/Tracing/Logging ｜ 评测流水线 ｜ 配置与密钥（Vault）｜ 备份与恢复演练
```

**边界规则（我最想强调的四条）**
① 模型永远不直接对业务系统写；② 检索必须在服务端做权限过滤（先过滤后排序）；③ 所有对外能力只有一个出口（网关 / executor），便于审计与替换；④ 平台不长期存业务数据副本。

### Step 2 · 数据流（两条主链路讲清楚）

**知识问答链**：用户提问 → 身份解析 → RAG：`principal + ACL 过滤 → 混合召回 → rerank → top-k（带 section/version/有效期）` → 网关（按任务路由到私有或云端模型）→ 答案 + `[n]` 引用 + 模型名 + 知识版本 + 时间 → 审计（问题摘要脱敏 + 命中文档 + 模型 + 延迟）→ 反馈按钮（采纳/有误）。
**数据分析链（Agent）**：提问 → 网关判断是否需要工具 → `tools/list`（按角色裁剪！）→ 模型请求 operation → **executor：权限 → 参数二次校验 → 执行（timeout/限流）→ 结构化双视图** → 回填 → 答案（数字来自工具，不来自模型）→ 审计 + 指标。
两个设计点：数字/事实一律不靠模型口算（工具给什么答什么，并把 payload 一并留档）；失败也进同一条链，`status` 与 `error_code` 可数。

### Step 3 · 安全与合规（这是企业平台的入场券）

- 身份：接企业 SSO；token 短时效；平台不落业务系统大账号；
- 授权：路由 + 工具 + 数据三层，全部 fail-closed（未知角色 = 最受限，未认证 = 拒绝）；
- 数据分级与出域控制：云端 API 调用前做脱敏与白名单字段；高密级只允许私有推理；
- 提示注入：外部内容（文档、网页、MCP server 描述）一律标为不可信；工具白名单 + 服务端强制权限，让「模型被说服」不直接等于「动作被执行」；
- 审计：不可篡改（append-only + 定期哈希锚定）+ 保留期 + 访问审计（看审计本身要权限并留痕）；
- 密钥：不进 Git、不进镜像、不进日志/审计（我 Demo 里的 denylist 就是这个思路的最小版）；
- 人工兜底：安全/工艺相关结论必须显示「依据哪份文件哪一条 + 版本 + 有效期 + 责任人字段」。

### Step 4 · 失败处理（按「谁挂了」枚举，不说「做高可用」这种空话）

| 故障 | 期望行为 |
|---|---|
| 模型不可用 | 明确 5xx + 审计 + 告警；**不静默降级**；允许按策略排队或用备用模型（响应与审计中标 `degraded`） |
| 推理慢 | 超时预算 + 进度提示 + 可取消；尾部延迟 P95 告警 |
| 检索挂了 | 退回「仅模型已知」并**显著标注无引用**（或直接拒答，按场景策略） |
| ERP/OA 超时 | 熔断该工具（暂时不进可选集）+ 答案标注「未取得业务数据」 |
| 索引与文档不一致 | 对账任务 + 孤儿 chunk 报警（过期制度被引用是安全事故） |
| 审计写不进 | 关键操作 fail-closed（宁可不服务也不能无痕），普通读操作可降级为日志 + 告警 |
| 单点/机器宕 | 数据备份 + 恢复演练（**没演练过的备份不算备份**）；两节点 + LB 是我会争取的第一项 |

### Step 5 · 监控与运营（平台是否被用、是否可信，都由这层回答）

- 系统：QPS、P50/P95、错误率与错误码分布、模型/工具调用次数与失败率、GPU/CPU/内存、队列积压；
- 成本：按部门/模型/token 的用量与费用归因（JD 第 5 条「结合成本和效果」的落地前提）；
- 质量：拒答率、空召回 top query、引用一致率抽检、用户反馈（采纳/有误）、评测集回归分数；
- 安全：权限拒绝次数与来源、异常批量拉取、登录失败分布；
- 采用度：周活跃部门、高频问题主题、被引用最多的文档（=该重点维护的资产）。
**关键一条**：评测集与知识库快照一起版本化，否则分数不可比。

### Step 6 · 分阶段落地（每阶段结束都有「有人在用」的东西）

**第一阶段（约 4–8 周）：知识库 + RAG + 模型网关 —— 建立信任**
- 范围：制度/操作规程/安全预案/设备文档（由内容 owner 批准入库）→ 带引用问答；模型网关接入 1–2 个 provider（含 1 个私有推理）；SSO + RBAC；审计 + 指标 + Docker 部署；错误信封。
- 不做：任何写操作、任何 DCS/PLC 相关、自由 SQL、多 Agent、K8s。
- 成功判据：内容 owner 认可答案口径；引用可点开核对；无权限用户拿不到受限文档（有负例测试）；周活跃部门 ≥2。
- **为什么从这里开始**：只读、可验证、失败代价低、见效最快，能在几周内建立组织信任，同时把网关/权限/审计这三件长期资产立起来。

**第二阶段（约 2–3 月）：ERP/OA 只读 Agent —— 业务分析**
- operation 白名单 + 只读视图 + 身份映射 + 限流/超时 + 口径对账（与既有报表比对）。
- 成功判据：数字与报表一致率 ≥ 业务方认可；单次查询不拖慢源库。

**第三阶段（约 3–6 月）：安全与设备数据分析 —— 辅助决策**
- 隐患/事件统计与趋势、设备维修记录检索与异常提示、HSE 知识助手。
- **仍然不做控制**：不接 DCS 写、不给联锁建议的自动执行、不自动开整改单（最多产出 proposal 给人审批）。
- 成功判据：安环部门把它纳入日常流程（而不是试用）。

**第四阶段（持续）：评测、模型路由、成本控制**
- 评测流水线（回归 + 影子对比 + 线上抽检）、按任务路由（分类/抽取走便宜模型）、配额与成本看板、密钥与镜像治理、必要的横向扩展（多副本、队列、共享索引服务）。

### Step 7 · 我会明确反对的第一版动作（这一段是这题的加分点）

- **不做「先接 DCS 控制」**：`[MY DESIGN]` 我的答案里没有这一项，也不该有。控制回路属于 DCS/PLS 与持证人员，AI 做分析辅助（详见 §12/§13）。
- 不在第一版上 K8s / 微服务 / Kafka / Redis（先单节点可备份可回滚）。
- 不做「全员自由提问再治理」（内容准入必须先有 owner）。
- 不把评测推迟到最后：第一阶段就要有 50–100 条基线评测集。

### Step 8 · 收尾话术（30 秒）

「我的排序是：先用网关 + RAG + 权限 + 审计把信任地基搭起来，第二阶段用 operation 白名单接 ERP/OA 做分析，第三阶段进安全与设备数据，评测和成本治理作为第四阶段持续做。每一阶段结束都必须有真实的部门在用，而不是一个技术 demo。整个过程中有三条线我不动：模型不直接写业务系统、检索在服务端做权限、每个能力只有一个可审计的出口。」

#### My Project Evidence

- 这条链的每一段我都有最小实现：`app/gateway/`、`app/rag/`、`app/agent/`、`app/agent/tools/erp.py`（operation 白名单形状）、`app/auth/`（两族权限）、`app/observability/`（request_id + 审计 + 指标）、`docker-compose.yml`
- 分阶段落地与我真实的开发节奏一致：Day1 网关 → Day2 RAG → Day3 Agent → Day4 平台化 → Day5 产品化（`SPEC.md`、`git log`）

#### Pitfalls

- 不要一上来画十个框。先问需求，再画一条能讲清数据流的主链。
- 不要把「接入 DCS 做智能控制」当作亮点。**JD 里也没有这一条**（`[FACT]` JD 六条职责不含工业控制）。
- 不要给没有判据的里程碑（每个阶段一个「谁在用 + 怎么算成功」）。
- 不要说「我会参考恒光现有的 XX 系统」——我不知道有什么系统，只能说「入职后先摸清现状」。

#### Interview Keywords

`four phases with users at each gate` `one egress per capability` `server-side ACL at retrieval` `no direct industrial control` `eval from phase 1`

---

# 12 · 化工行业 AI 场景

> 通用要求：每个场景必须讲清「AI 做什么 / AI 不做什么 / 数据从哪来 / 谁验收」。
> 本节所有关于恒光具体现状的表述均标 `[FACT]`（公开可查）或 `[INFERENCE]`（我的推演）。
> `[FACT]` 公开资料显示公司主营硫化工、氯化工产品链，含烧碱/盐酸/硫酸/氯酸钠/三氯化磷/三氯化氢硅等多类产品，布局怀化、衡阳、老挝三大基地（来源：公司官网公开简介与 2025 年年度报告摘要，见 §来源，检索时间 2026-10-01）。
> `[FACT]` 公开资料显示怀化基地推进「工业互联网 + 危化安全生产」与智慧工厂平台建设，申报省级 5G+工业互联网示范工厂（来源：公司官网公开页面汇编）。
> `[INFERENCE]` 因此「已有部分信息化/安全数字化基础 + 需要一层统一的 AI 能力层」是一个合理的岗位背景判断；具体系统清单需入职后核实。

## Q12-01 企业知识类场景（SOP / 操作规程 / 安全制度 / 应急预案 / 设备文档 / 研发资料）

#### Short Answer

这是我认为的第一个落地场景：AI 做「可引用的检索 + 摘要 + 差异对比 + 培训问答」，不做「现场处置决定」。

#### Standard Answer

**AI 做**：按岗位/装置定位到具体条款并给引用（文件 + 章节/条 + 版本 + 生效日期）；把长制度摘要成要点；多版本文档的差异提示；新员工培训问答；「这个问题归哪份制度管」的导引。
**AI 不做**：不替代正式文本（回答必须显示「以制度原件为准」并给出处）；不推断未写进制度的处置动作；不回答超出知识库范围的问题（明确说「没有足够信息」并指向责任人）。
**数据与前提**：制度有权威版本与 owner；谁能批准入库/下线必须是流程；元数据（版本、生效日期、适用范围/基地/装置）比正文更难搞但更重要。
**权限**：研发配方类文档默认高密级、默认不进模型上下文（`[PRODUCTION_NEXT]` 云端 API 场景下要单独决策，甚至只允许私有推理）。
**验收**：内容 owner（而非 IT）签字；引用可点开核对；空召回有清单可反推缺哪些文档。
**为什么排第一**：只读、见效快、失败代价最低、且它顺带把内容治理、权限、审计三件长期资产建起来——后面的 ERP 与安全场景都靠这三件东西。
**我的 Demo 对应**：`[MY DESIGN]` 我用公开资料（公司简介 + 定期报告摘要 + 公开新闻）做了同一条管线：heading 感知 chunk → 带 section 的引用 → 无依据拒答（`app/rag/`、`data/documents/`）。语料换了，形状没换。

#### Follow-up Questions

- 制度之间互相矛盾怎么办？（并列引用 + 版本/适用范围 + 提示冲突 + 升级到 owner，模型不裁决）
- 一线工人不用键盘怎么办？（移动端 + 语音 + 极短答案 + 引用可展开）
- 你要如何度量这个场景做成了？（检索成功率、引用点开率、空召回下降、一线主动使用频次）

#### Interview Keywords

`provenance over fluency` `version + effective date metadata` `owner signs off`

---

## Q12-02 安全类场景（隐患分析 / 风险统计 / 事故分析 / HSE 知识助手）

#### Short Answer

安全数据适合做「统计、归类、趋势、对比、材料起草」这类分析辅助，不适合也不应该做「实时报警、处置指令、风险等级自动判定」。

#### Standard Answer

**AI 做**：隐患台账的自然语言查询（哪类隐患增长、哪个区域集中、闭环率多少）；按类别/严重度/区域的分布与趋势解读；历史事故报告的检索与共性归因线索（「类似描述历史上出现过哪些」）；制度符合性初筛（给条款 + 现场记录的差异点让人判断）；辅助起草整改通知、培训材料、专项检查清单草稿。
**AI 不做（明确列出）**：不产生实时报警、不改报警阈值、不判定「可以开工」、不下达处置指令、不替代风险辨识评审（HAZOP/工作安全分析要人做）、不把模型生成的分类当成统计口径的唯一真相。
**为什么这条边界比别的场景更重要**：`[INFERENCE]` 危化企业的安全管理有法定责任体系与持证人员要求（如注册安全工程师，`[FACT]` 公开的公司岗位信息里出现「注册安全工程师证书者优先」），一个「AI 说的」不能作为免责依据。所以我要的是**建议 + 引用 + 责任字段留给人**，并且建议必须显示知识版本与时间。
**数据现实**：安全事件描述是自由文本，字段化质量决定分析质量。我会先做「数据体检」（缺失率、同义表述、区域命名不统一），因为这一步通常比模型更能提升结论质量。
**我的 Demo 对应**：`[MY DESIGN]` `safety_incident_analysis`（5 个固定 operation：按区域/严重度/类别统计、最近高风险、按周趋势），参数只有 `operation/days/limit/area`，SQL 全部固定；数据是合成的（`data/synthetic`），payload 里带 `data_source` 与 disclaimer。operator 和 manager 都能用（安全分析面向一线是有意的角色设计），ERP 则限定 manager/admin。

#### Follow-up Questions

- 隐患描述文本要做自动分类，你担心什么？（分类结果不能进法定口径；必须与既有类别对齐并可人工纠正，且保留原文引用）
- 安全数据接入需要什么前置？（只读通道 + 分级授权 + 事件描述里可能含人员信息 → 脱敏）
- 如果模型给出的归因和业务经验相反怎么办？（呈现两种说法 + 引用 + 交给人；平台不做裁决）

#### Interview Keywords

`analysis not alarm` `responsibility field stays human` `data health before model`

---

## Q12-03 ERP 类场景（采购 / 库存 / 供应商 / 经营分析）

#### Answer

**AI 做**：自然语言 → 固定 operation 的查询与解读（采购额 top 物料、价格变化、供应商集中度、低于安全库存的物料、消耗与采购量对比）；异常波动的提示（不是根因结论）；周期报告草稿与图表底稿；跨口径对照表（同一数字在不同报表里的来源）。
**AI 不做**：不做写操作（不提采购申请、不改价格、不动库存）；不生成 SQL；不做「建议向某供应商下单」这种带商务决策与合规风险的结论（最多呈现数据 + 既有制度条款）；不预测价格（除非有专门的时序模型与业务验收，且明确标注为模型输出）。
**我的实现对应**：`[MY DESIGN]` `erp_purchase_analysis` 7 个 operation，`days 1–365`、`limit 1–50`，参数绑定 + 固定 SQL（`app/db/queries.py`），双视图输出（模型读文本块，最多 8 行；平台读完整 payload）。
**为什么这些 operation 而不是别的**：`[MY DESIGN]` 它们是我按「业务问题 → 一次可答的聚合」倒推的：`purchase_amount_stats`（品类占比）答「钱花在哪」，`purchase_price_trend`（前后半段均价）答「涨没涨」，`inventory_summary`（快照 + 安全库存对比）答「会不会断料」。真实接入时 operation 应该继续按这个方式扩展，一个 operation = 一个可验收的业务问题 = 一条测试。
**权限**：`[FACT]` JD 明确要接 ERP/OA。经营数据（成本、毛利、供应商价格）在化工企业是敏感数据，`[INFERENCE]` 我会坚持经营明细默认只对财务/采购与授权管理者可见，并且 AI 平台不长期存副本。
**成功判据**：数字与既有报表一致率；一次查询的 P95 与源库负载；业务方是否把 AI 查询写进他们的例会流程。

#### Interview Keywords

`one operation per verifiable business question` `read-only contract` `no commercial decision`

---

## Q12-04 设备类场景（维修记录 / 设备知识库 / 异常分析）

#### Answer

**AI 做**：设备台账与维修记录的检索问答（这台设备历史上出现过什么、上次检修换了什么、说明书里这个报警码怎么说）；故障描述的归集与相似案例推荐（「类似现象历史上出现过 N 次，处理记录在这里」）；检修规程/备件清单查询；故障趋势统计（按设备/区域/故障类别）；报告与工单描述草稿。
**AI 不做**：不做在线状态监测的判定（那是 PHM/报警系统）、不自动生成检修指令、不替代设备工程师的失效分析结论、不自动下采购备件单。
**落地路径**（我认为的顺序）：先做**文档层**（说明书/检修规程/事故案例 → RAG），再做**记录层**（维修工单 → 结构化统计查询，走 operation 白名单），最后才评估**预测层**（时序特征 + 专门模型）。前两层的价值/风险比明显更高，且不需要新的实时数据通路。
**我的 Demo 对应**：`[MY DESIGN]` 我已经在合成库里建了 `equipment`（6 条）和 `maintenance_records`（6 条）两张表并有测试覆盖，但**没有**暴露设备工具——这是有意留的：它是我认为最小成本就能扩出的第 5 个工具（继承 `BusinessQueryTool`，只需 args_model + operations 映射）。我会把它作为「入职后第一个可复用扩展点」讲出来，而不是假装已经做了。
**一个真实提醒**：设备文档通常是扫描件 + 图纸 + 表格，OCR 与表格还原质量会直接决定这个场景的上限。我第一阶段就要把「文档质量」当成一等工程问题，而不是指望模型兜住。

#### Follow-up Questions

- 维修记录里同一台设备有五种写法怎么办？（先建主数据映射，映射比模型重要）
- 报警码手册是表格，你的 chunker 能处理吗？（当前按文本切，表格是我的已知弱点 → 需要表格感知的分块/结构化）
- 预测性维护什么时候值得做？（有足够长的历史 + 明确失效样本 + 业务方愿意接受误报率）

#### Interview Keywords

`docs → records → prediction` `master data mapping` `scan/table quality`

---

## Q12-05 生产数据 / DCS 类场景（时序数据 / 异常检测 / 辅助决策）

#### Short Answer

可以做**只读分析**：取历史点位数据做趋势、关联、异常提示、报告解释。不可以做**控制**：不写设定值、不下发指令、不参与联锁。这条线我按架构而非按口头承诺来保证。

#### Standard Answer

`[FACT]` 公开资料显示公司在怀化基地推进「工业互联网 + 危化安全生产」与智慧工厂平台，运用工业互联网、大数据、5G 等技术。（来源：公司官网公开信息汇编；检索时间 2026-10-01）
`[INFERENCE]` 如果这些信息化基础存在，那么「时序历史数据 + AI 分析」是自然的下一步；具体系统、点位、接口需入职后核实。

**AI 做什么（第四阶段以后）**：
- 通过**单向只读**数据通道（历史库/historian，经网闸或独立采集侧）取聚合后的点位统计；
- 趋势与关联分析：某参数与上下游参数的偏离、异常时段的历史复盘；
- 自然语言 → 受限查询（设备/点位白名单 + 时间窗 + 聚合粒度，同样固定 operation）；
- 异常提示：由**传统算法/规则/时序模型**产生，LLM 只负责「把结果讲成人话 + 附历史相似案例 + 引用」；
- 值班报告草稿、班次对比、能耗与物料平衡核算底稿。
**AI 不做什么（明确列出）**：不下发设定值、不写任何 DCS/PLC 点、不参与联锁与安全仪表功能、不输出「可以旁路/可以解除报警」的建议、不实时闭环控制、不把 LLM 当作报警判定器。
**为什么这么定（不只是「安全第一」）**：① 确定性要求：控制回路的时序与失效模式是工程化验证过的，LLM 无法给出可验证的最坏情况界限；② 责任要求：处置必须由持证岗位人员作出并可追责；③ 技术现实：LLM 不做数值判定也更有优势，把它的比较优势限制在「检索 + 解释 + 成文」，反而是这个岗位能长期交付价值的方式。
**架构保证方式**：工具白名单里根本没有写类工具（`[MY DESIGN]` 我 4 个工具全是只读）；数据通道单向（历史库在控制网外侧，只出不进）；权限矩阵中「与生产控制相关」的任何能力面不存在，因此不可能被越权调到。这是我理解的「边界不靠口头承诺」。

#### Follow-up Questions

- 那异常检测你用什么？（优先统计/规则/专用时序模型，可验证性远高于 LLM；LLM 只做解释层）
- historian 取数会不会拖慢生产网？（只做聚合、限流、只读副本）
- 如果业务要求「至少给个操作建议」？（可以给**制度内**的建议：来自 SOP 检索并引用 + 明确标注「需岗位人员按规程确认」，绝不自创处置）

#### Interview Keywords

`read-only historian` `LLM explains, deterministic models detect` `control plane excluded by architecture`

---

## Q12-06 研发类场景（专利知识库 / 工艺资料 / 历史问题）

#### Answer

**AI 做**：公开专利/文献检索与整理（现有技术梳理、按主题聚类、竞品公开动态摘要）；内部研发文档与历史问题的可引用检索（「这个配方问题历史上出现过吗、当时的处置记录在哪」）；实验记录与报告的成文底稿、格式规范化；小试/中试公开资料层面的规程查询。
**AI 不做**：不判定技术新颖性/可专利性（那是代理人和研发人员的判断）、不做配方或工艺路线推荐（最敏感的知识产权）、不向云端 API 提交未公开配方/工艺参数、不把「模型总结」当成技术结论。
**数据边界（这里最需要小心）**：`[INFERENCE]` 研发未公开资料是化工企业最核心的商业秘密，默认应该是「不入任何可能出域的路径」，包括：不进云端模型、不进可被广泛检索的知识库、不进日志与审计正文。`[PRODUCTION_NEXT]` 做法：研发域单独一套私有推理 + 单独 collection/库 + 独立密级 + 白名单人员 + 更严的导出控制（禁复制、水印、只给引用不给全文）。
**我的 Demo 对应**：`[MY DESIGN]` 我的语料全部标注了 `source: public` 且带 URL，回答策略里明确写了「本项目只使用公开资料，回答不构成投资建议」（`app/rag/prompt.py`）。同样的字段结构可以直接承接一个 `classification: internal|secret` 元数据维度——这是我认为该在 schema 上就预留的东西，而不是靠事后过滤。

#### Follow-up Questions

- 怎么防止「检索没命中但模型凭记忆说了同行配方」？（域白名单 + 引用强制 + 无据拒答 + 输出侧敏感词/实体检测）
- 专利分析你会用 LLM 做什么？（分类、聚类、对比表填充——判新颖性不做）
- 研发人员会想要什么但你不该给？（「帮我改配方」类生成需求）

#### Interview Keywords

`secret never leaves private inference` `novelty judgement stays human` `classification field reserved in metadata`

---

# 13 · 为什么化工企业的 AI 特别需要安全边界

## Q13-01 大模型可以直接控制化工生产吗？

#### Short Answer

不能，也不该由我这样的平台去尝试。在这个 Demo 里我的答案是**不做**：AI 负责检索、分析、解释、辅助决策；DCS/PLC 负责控制；关键确认、审批和操作由人负责。

#### Standard Answer

**我的分工表（面试时可以直接写在这块区域）**

| 层 | 承担者 | 责任 |
|---|---|---|
| 语义层 | AI 平台 | 检索制度/资料、查询业务数据、统计与分析、解释、起草、提示待关注项 |
| 控制层 | DCS / PLC / SIS | 回路控制、联锁、安全仪表功能 |
| 决策与执行层 | 持证岗位人员 / 管理者 | 确认、审批、现场操作、例外处理 |

**三条理由（不是「AI 还太弱」这一句）**：
① **可验证性**：控制回路的正确性靠工程验证与确定性分析（SIL 定级、联锁逻辑验证、最坏情况界限）。LLM 是概率输出，无法给出可证明的最坏情况边界。这不是训练量问题，是方法论不匹配。
② **责任与合规**：`[FACT]` 公开资料显示公司以安全环保为经营底线；`[INFERENCE]` 危化生产的责任体系要求关键操作由具备资质的人员按规程执行。一个「AI 建议」无法成为责任主体，所以**责任必须在人**，而系统必须让「人知道自己是责任者」：引用、版本、有效期、责任人字段。
③ **失败模式不同**：控制故障要求「安全状态」，LLM 的典型失败是「自信地输出错内容」——它不会把自己切到安全状态，只能靠外围工程。
**我怎么把这条边界做成架构而不是口号**（`[MY DESIGN]`）：
- 工具白名单里**没有任何控制类工具**：4 个工具全是只读（`knowledge_search` / `document_lookup` / `erp_purchase_analysis` / `safety_incident_analysis`）；
- operation 是固定枚举 + 参数化查询，模型无法表达任何「写」的动作；
- `ToolExecutor` 在数据访问**之前**做权限检查，未认证即拒绝（fail-closed）；
- 每次工具调用（包括被拒的）都落审计，`X-Request-ID` 可全链回溯；
- 系统提示里明确「只使用工具返回的事实、无依据时明确说明、不得假装调用不存在的工具」；
- 输出里带来源与「以制度原件为准」性质的约束（RAG 回答策略）。
如果连不上，就永远不可能被越权调到高危接口——这比「我们很小心」更有说服力。

**Human-in-the-loop 的四个具体机制**（对应 `[PRODUCTION_NEXT]`，设计见 Q8-12）：
1. 建议与执行分离（Agent 只能产出 proposal）；
2. 参数快照 + 人工批准（人看到什么就执行什么）；
3. 权限双查（路由 + 工具）+ 未认证 fail-closed；
4. 全程可追责（request_id 链 + 模型名 + 引用）。

**我会主动说的一个「灰色地带」**：只读分析里的「异常提示」如果做得太实时、太像报警，就可能事实上参与操作决策。我的处理是：这类提示必须带「非控制信号 / 仅供参考」的明确标注，并且与报警系统在同一界面区分开；重要参数异常优先由确定性的规则/统计模型给出，LLM 只做解释。

#### Follow-up Questions

- 如果以后 AI 平台确实要参与控制，你认为需要满足什么条件？（我不认为「AI 平台」应该进控制回路；真要闭环也应该由通过认证的控制系统实现，AI 最多提供设定值建议并被人在回路确认）
- 一线员工会不会绕过你？怎么防？（把「不用引用/无依据」的答案直接标为不可用，让绕过变得没好处，比制度更管用）
- 你怎么跟业务方解释「AI 不给直接答案」？（给的是「有出处的答案 + 该找谁」，这比无出处的答案更快）

#### Pitfalls

- **绝对不要提「先接 DCS 做智能控制优化」当作方案或亮点**。`[FACT]` JD 六条职责里没有工业控制；把它当成加分项是面试里的重大判断失误。
- 不要说「我们会做严格审核所以安全」。要说架构上不可达 + 可追责。
- 不要为了显得懂化工而编造专业细节（工艺参数、联锁逻辑）。不知道就说不知道，然后把工程原则说清楚。

#### Interview Keywords

`analysis not control` `architecturally unreachable` `human-in-the-loop` `accountability + provenance`
# 14 · RBAC

## Q14-01 权限模型怎么设计的？

#### Short Answer

一张写死的角色—权限矩阵，**两族互不继承的权限**：API 权限（`chat:run`、`knowledge:ingest`、`audit:read`…）由 FastAPI 依赖强制，工具权限（`tool:erp`、`tool:safety`、`tool:knowledge`）由 ToolExecutor 强制。角色三个：admin / manager / operator。

#### Standard Answer

`[MY DESIGN]` `app/auth/permissions.py` 的模块文档就把这个分族写成了设计声明：**「能调这个端点」和「能用这个工具」必须能被独立授予；工具永远不继承路由的权利，反之也一样。**
矩阵（`ROLE_PERMISSIONS`）：
- `admin` = `ALL_PERMISSIONS`（`frozenset(Permission)`，即全集，新加枚举自动落入 admin——这是有意为之，因为 admin 应当能看到全部能力面）；
- `manager` = chat + models + knowledge:query + agent:run + **audit:read** + tool:knowledge + tool:erp + tool:safety；
- `operator` = chat + knowledge:query + agent:run + tool:knowledge + tool:safety。
两个我认为值得讲的判断：
① **operator 有 `tool:safety` 但没有 `tool:erp`**。理由是安全事件数据面向一线是有意义的（班组长就该能问「我们区域最近有什么高风险」），而采购金额/供应商数据不该对一线开放——**权限矩阵的价值在于它体现业务判断，不是把三个角色平均分配**。
② **`audit:read` 给 manager**，因为「谁能看审计」是审计体系能不能被信任的一部分；同时审计读取**本身也是一条审计记录**（`audit.read`），我防的是「管理者无痕地翻看别人」。
身份来源是固定 bearer token（`app/auth/auth.py`，三个 demo token），`CurrentUser` 是 frozen dataclass。文件里的注释是我认为最要紧的一条纪律：**未知或缺失 token 永远不允许继承 admin 角色**——未认证流量保持未认证，API 答 401。

#### My Project Evidence

- `app/auth/permissions.py`（两族权限 + 矩阵 + `Permission` StrEnum）
- `app/auth/auth.py`（`DEMO_USERS`、`CurrentUser`、`authenticate`）
- `tests/unit/test_permissions.py`（39）+ `tests/integration/test_rbac.py`（32）
- `[FACT]` `SPEC.md` §9（角色矩阵来源）
- 演示：`DEMO_SCRIPT.md` Step 5/6（curl 三个 token 打同一个端点）

#### Follow-up Questions

- 为什么不用 Casdoor/Authentik？（`[PRODUCTION_NEXT]` 生产一定有 SSO；我的抽象是 `CurrentUser`，替换的是 `get_current_user` 内部，依赖签名与全部 `require()` 不动——这是我唯一真正拿到的「抽象红利」，见 §23 Q23-04/05/06）
- 100 人 10 部门怎么扩？（角色矩阵会立刻失效：需要 **部门/基地维度 + 数据范围 + 用户组**，矩阵变成规则表并可管理界面维护；权限判定加缓存但要有失效通道）
- 为什么没有 ABAC？（我没有做，也不声称做过；`[PRODUCTION_NEXT]` 的形态是「角色 + 属性（基地/部门/密级）联合判定」，而不是替换 RBAC）

#### Pitfalls

- 不要说「我们用了 RBAC 所以知识库是安全的」——文档级 ACL 我没做（Q7-14）。
- 不要说「支持自定义角色」。角色是代码常量，加角色要改代码与测试——这是本期范围，我如实说。
- 不要把 demo token 当成「安全设计」。它们是公开演示凭据（`.env.example` 与 README 里就写着），真正的设计点是「未知 token 不继承特权」这条纪律。

#### Interview Keywords

`two permission families` `role matrix in code` `no privilege inheritance` `audit read is itself audited`

---

## Q14-02 为什么 API 和 Tool 要分别检查权限？

#### Answer

见 **Q5-06**（完整论证 + 三种绕过场景 + 双层检查的顺序理由）。
补充两点本岗位视角：
① 这个设计对**企业集成**是必要的，不是洁癖。接了 ERP 之后，「谁能通过 AI 看采购数据」就是一个独立的授权决定，它不该跟着「谁能用聊天窗口」漂移。我把这条独立性写进矩阵（`tool:erp` 与 `chat:run` 是两个格子），所以将来业务说「AI 能用，但只有采购经理能查价格」时，我改一行矩阵就能落地。
② 顺序上我的 executor 是 **白名单 → 权限 → 参数校验 → 执行**：先判「能不能用」再判「参数对不对」，所以未授权者拿不到字段级校验反馈（不泄露 schema 细节），而被拒时审计已经落盘。
③ **前端不做判断**：Web Console 的角色下拉只换 Authorization header；`tests/integration/test_web_console_contract.py::test_models_is_403_for_operator` 钉住后端不配合前端的假设。

---

## Q14-03 operator 能做什么、不能做什么？

#### Short Answer

能做：聊天、知识问答与检索、跑 Agent、用 `knowledge_search` 与 `document_lookup` 与 `safety_incident_analysis`。不能做：查 ERP 采购/库存数据、导入文档、读审计、列模型清单、看用户目录。

#### Standard Answer

`[MY DESIGN]` 按 `ROLE_PERMISSIONS[ROLE_OPERATOR]` 精确列（这张表我可以白板上写出来）：
| 能力 | 端点/入口 | operator |
|---|---|---|
| 聊天 | `POST /api/chat`（`chat:run`） | ✅ |
| 知识检索/问答 | `POST /api/knowledge/search`（`knowledge:query`） | ✅ |
| 跑 Agent | `POST /api/agent/run`（`agent:run`） | ✅ |
| 工具 `knowledge_search` / `document_lookup` | `tool:knowledge` | ✅ |
| 工具 `safety_incident_analysis` | `tool:safety` | ✅ |
| 工具 `erp_purchase_analysis` | `tool:erp` | ❌ `PERMISSION_DENIED` |
| 导入文档 | `POST /api/knowledge/ingest`（`knowledge:ingest`） | ❌ 403 |
| 读审计 | `GET /api/audit`（`audit:read`） | ❌ 403 |
| 列模型/工具 | `GET /api/models`（`models:list`） | ❌ 403 |
| 用户目录 | `GET /api/users`（`users:manage`） | ❌ 403 |
`[MY DESIGN]` **最该被注意的行为是「部分拒绝返回 200」**：operator 问 ERP 问题时，`agent:run` 权限通过 → 模型可以请求 `erp_purchase_analysis` → executor 在工具层拒 → 响应 200，`tool_calls[0].error_code = "PERMISSION_DENIED"`，答案里包含一个「我没拿到数据」的说明。审计里这条运行记 `denied_calls=1`；只有当**全部**工具调用都被拒且没有任何成功时，整条 `agent.run` 才记 `status=denied`（`app/api/agents.py`）。
**为什么不改成 403**：因为 Agent 的这次运行确实完成了——用户没有被欺骗（明确告诉他数据没拿到），而平台侧「谁试过越权」被完整记录。把一次成功的运行降级为 403 会毁掉「谁在试探边界」这条最有价值的审计信号。

#### My Project Evidence

- `app/auth/permissions.py::ROLE_PERMISSIONS`
- `app/api/agents.py`（`denied = [call for call in result.tool_calls if …]` 与状态判定）
- `tests/integration/test_rbac.py`（32 个测试，逐格钉住矩阵）
- `tests/unit/test_agent_permissions.py`（14）

#### Follow-up Questions

- 你会给一线工人一个不同角色吗？（会——车间角色应该连 `chat:run` 的自由文本都收窄成场景化入口，且工具集只留安全与设备类；这是我按 `[FACT]` JD「车间」与机关差异做的推演）
- 越权尝试怎么报警？（`permission_denied_count` 指标 + 按 user/role 的滑窗阈值 → 通知 owner；我已有计数，没有告警）

#### Pitfalls

- 不要把 `models:list` 说成人人都能访问——**它只有 admin/manager 能看**（我刻意让能力目录本身成为受保护信息）。

#### Interview Keywords

`partial denial is 200 with error_code` `capability catalog is protected` `matrix per cell tested`

---

## Q14-04 如果用户有 100 人 / 10 个部门怎么扩展？

#### Short Answer

固定角色矩阵撑不到那里。第一步是「角色 + 组织属性」双维判定并引入用户组与数据范围；第二步是权限从代码常量迁到可管理的存储并带版本号；身份本身换成 SSO。

#### Standard Answer

`[PRODUCTION_NEXT]` 我的演进顺序（尽量小步，每步都有可交付）：
**Step 1｜身份换成真来源，权限形状不动（1–2 周）**
把 `get_current_user` 内部从「查表 token」换成 OIDC/LDAP 会话校验。`CurrentUser` 增加 `department` / `base`（基地）属性，其余代码不动——**这是我这套抽象唯一真正挣到的东西**，我会老实说这是抽象的红利而不是我的远见。
**Step 2｜授权判定从「角色 ∈ 矩阵」变成「主体 → 一组属性 → 规则」**
`has_permission(subject, permission)`，subject 携带 role + department + base + group。规则表存 DB（`role_permissions` / `group_permissions` / `user_groups`），带版本与变更审计。这一步必须配**管理界面 + 变更人留痕**，因为权限变更本身是高危操作。
**Step 3｜数据范围（这是企业里真正的分水岭）**
光有「能不能用 ERP 工具」不够，需要「这个 operation 只能看自己基地的数据」。做法是把范围条件注入查询（`AND base = :actor_base`）而不是靠上层过滤——**范围必须是查询的一部分，不能是结果的一部分**。这一步同时解决 Q7-14 的文档级 ACL，因为它俩是同一个机制（服务端注入 + metadata 过滤）。
**Step 4｜工具级与 operation 级细粒度**
`tool:erp` 拆成 `erp:summary` / `erp:order_detail`；`Tool.permission` 从单值变集合（`any` 判定）。
**Step 5｜性能与一致性**
判定结果按 `subject_version` 缓存，但**必须有失效通道**（撤权立刻生效）；判定与拒绝都保留审计；每次发布跑一遍「权限矩阵快照测试」（我有 39 + 32 个测试打底，扩展时逐格加）。
**我不做的事**：不把权限塞进 prompt 让模型「自己判断该不该答」（那是最典型的 fail-open）；不做「临时给用户加个权限」的口头流程（无留痕的授权在企业里就是事故原因）。

#### My Project Evidence

- 扩展点已经明确：`app/auth/dependencies.py::get_current_user`（唯一身份入口）、`app/auth/permissions.py`（唯一矩阵）、`app/agent/executor.py`（唯一工具判定处）
- 回归保护：`tests/integration/test_rbac.py`（32）、`tests/unit/test_permissions.py`（39）
- 缺口：`CurrentUser` 无部门/基地字段、无 group、无缓存、无版本（→ §22）

#### Follow-up Questions

- 权限判断能不能缓存？缓存的代价是什么？（能，但撤权生效延迟就是泄露窗口；我会缓存到「会话 + 版本」粒度并给主动失效）
- 10 个部门会不会需要 10 套角色？（不应该。角色表达职责，部门是数据范围；如果开始为部门造角色，说明我把两个维度混了）
- 怎么防止权限只增不减？（定期「权限体检」：拉出长期未使用的授权 → 回收；这是治理动作，也是 `[FACT]` JD 第 6 条「平台使用规范」的实际内容之一）

#### Pitfalls

- 不要吹「我的 RBAC 能直接扩到 1000 人」。矩阵是 `Final` 常量，加角色要改代码——这是本期范围，先承认再讲演进。
- 不要说「ABAC 更高级所以该上 ABAC」。要给触发条件（组织维度、数据范围需求出现）。

#### Interview Keywords

`identity swap is the only clean seam` `scope injected into query` `revocation must be immediate` `matrix snapshot tests`
# 15 · Audit

## Q15-01 审计日志记录什么？

#### Short Answer

记「谁、在什么时候、通过哪个入口、用了哪个模型/工具、结果是什么、花了多久」，以及一个 request_id 把这些串成链。**不记 prompt 正文、不记文档正文、不记任何凭据。**

#### Standard Answer

`[MY DESIGN]` 一张表两种行（`app/observability/audit.py`）：
**API 级**（当前真正落库的 4 类）：`chat.complete`、`knowledge.ingest`、`knowledge.search`、`agent.run`。
**工具级**：`tool.call`，一行一次工具执行（含被拒的）。
列（SPEC §5.2）：`user_id / request_id / action / endpoint / tool_name / model_name / mode / input_summary / status / latency_ms / created_at`。
`status` 是有限集：`success / error / denied / unauthenticated / not_found / conflict`。
`input_summary` 是唯一装业务细节的地方，而且它**不是自由字典**：写入前统一过 `sanitize_summary()`——
- `DENYLIST_TERMS`（`authorization / api_key / apikey / x-api-key / token / secret / password / content / text / chunks / prompt / messages`）命中的 key **直接丢弃**；
- 嵌套结构（dict/list/tuple/set）**只留长度**；
- 标量字符串**截断 160 字符**（`MAX_SUMMARY_VALUE_CHARS`）；
- 最多 12 个 key（`MAX_SUMMARY_KEYS`）。
`[MY DESIGN]` 这条「净化只写在一个地方」是刻意的：净化规则如果散在各端点，就一定有人漏写；集中在 `AuditLog.record()` 之后，新增端点无法绕过它。
三条我认为最有面试价值的行为设计：
① **被拒也记**：`app/auth/dependencies.py::require()` 里 403 之前先写一条 `status=denied`，注释写得很直白——「记录被拒的尝试正是有审计的意义」；
② **匿名不落库**：`audit_logs.user_id` 在 SPEC 里 NOT NULL，所以 401 这类无身份事件**只进内存 deque + 结构化日志**，不破坏表契约（我宁可显式承认「401 不在 DB 里」，也不用可空列把约束改掉）；
③ **审计写失败绝不打挂请求**：`record()` 里 `except Exception` → 记 `last_error` + `logger.warning`，主请求继续。

#### My Project Evidence

- `app/observability/audit.py`（`AuditAction`、`AuditStatus`、`DENYLIST_TERMS`、`sanitize_summary`、`record`、`record_api`、`record_tool_call`、`deque(maxlen=…)`）
- `app/auth/dependencies.py`（denied 先写后抛）、`app/agent/executor.py`（每次工具一行）
- `app/api/audit.py`（分页 + `tool/action/status/request_id/user_id` 过滤 + 未知 request_id → 结构化 404）
- `tests/unit/test_audit.py`（19）：`test_secrets_are_never_persisted`、`test_write_failure_never_raises`、`test_anonymous_events_stay_in_memory_only`

#### Follow-up Questions

- 为什么不记 prompt？（一次问答的正文可能含内部数据；`chars` + `request_id` 已经够定位事件。真要取证时应该走**受控的导出流程**，而不是让审计表变成全文检索库）
- 用户输入完全不记吗？（我现在只记长度/错误类型/参数摘要。生产上可能记 hash 用于同题聚合，但那是另一个决策）
- 谁能看审计？看审计要不要留痕？（**当前没留痕**，这是我清单上的第一优先补项）

#### Pitfalls

- 不要说「所有端点都写了审计」。只有 4 类 API 动作 + `tool.call`；`GET /api/knowledge/documents`、`GET /api/models`、`GET /api/audit` 只有鉴权没有留痕（`AuditAction` 里声明了 `models.list` / `audit.read` / `knowledge.documents` 三个常量但**没有对应写入**）。被追问时必须承认。
- 不要说「审计不可篡改」——它就是普通 SQLite 表（见 Q15-05）。

#### Interview Keywords

`one row per action` `denylist sanitization` `denied is recorded` `write failure never fatal`

---

## Q15-02 request_id 怎么串起来？

#### Answer

见 **Q5-07**（完整实现）。这里补三条常被追问的细节：
① **来源与生成**：`RequestContextMiddleware`（纯 ASGI）优先取调用方带来的 `X-Request-ID`，没有就生成 `req_<uuid4>`；写进 `scope["state"]["request_id"]`（给依赖用）+ contextvar（给日志用）+ 回写响应头。
② **一个 id 覆盖几行**：一次 operator 的 ERP 越权尝试会产生 `tool.call=denied` + `agent.run=success(denied_calls=1)` 两行，同一 request_id；再加鉴权层的拒绝就是三行。`GET /api/audit/{request_id}` 一次拿全链。
③ **信任边界**：接受客户端传入的 id 是**双刃**。我接受它的理由是内部 Demo 与可复现性（curl 时能自己指定）；`[PRODUCTION_NEXT]` 生产上我会：长度与字符集校验 + 只允许通过内部网关写入 + **绝不把它当授权或幂等键**（它是可伪造字符串）。这是我要主动说的一个设计代价。
④ **传播链**：`Actor.from_user(user, request_id)` 是唯一把身份与请求绑起来的构造函数，AgentRuntime 与 executor 只透传 `Actor`，不自己造 id——所以「谁在哪一步被记录了什么」只有一个来源。

#### My Project Evidence

- `app/observability/middleware.py`（`_incoming_request_id`、`send_wrapper` 回写头、`request_id_scope`）
- `app/observability/audit.py::Actor`（文档字符串直接写「the single correlation key」）
- `tests/integration/test_platform.py`（header 回显 + 全链一致）

---

## Q15-03 哪些操作需要审计？

#### Short Answer

**四类必审**：身份失败、授权拒绝、数据读取（谁查了什么范围）、能力变更（导入/配置/权限变更）。执行类动作和它们的失败也要审——「审成功」不是审计，「审发生」才是。

#### Standard Answer

`[MY DESIGN]` 我现在覆盖的（按优先级）：
1. `agent.run`（含 `steps / tool_calls / denied_calls / run_status` 摘要）——这是平台的主事件；
2. `tool.call`（每次执行一行，success / error / denied）；
3. `knowledge.search`（`top_k` + 结果数，不记 query 文本）；
4. `knowledge.ingest`（`documents` / `chunk_count` / `rebuild`）——**能力变更类**；
5. 路由层 403（`status=denied`，含 `required_permission` 与 `role`）。
`[MY DESIGN]` 我现在**没**覆盖但必须覆盖的：`GET /api/audit` 读取本身、`GET /api/models`（能力面侦察）、`GET /api/knowledge/documents`（文档清单本身就是元数据）、以及任何权限/配置变更事件。
判据我给一句话：**「这条信息被谁看过，将来需不需要回答」需要就是审计事件。** 三个只读端点里，`/api/audit` 是最该补的一个——质证的最后一条链断在这儿很难看。
`[PRODUCTION_NEXT]` 生产上我会再加：登录/登出（真身份体系下）、导出（把数据带出平台边界的行为）、模型与 provider 配置变更、知识库文档上下线、审批的发起与结论、以及**审计的读取与导出本身**。

#### My Project Evidence

- 现状清单：`app/api/chat.py`、`app/api/agents.py`、`app/api/knowledge.py`、`app/agent/executor.py`、`app/auth/dependencies.py`
- 缺口的直接证据：`app/api/audit.py`、`app/api/models.py` 里无 `record_api` 调用
- `AuditAction` 已声明未使用：`KNOWLEDGE_DOCUMENTS` / `MODELS_LIST` / `AUDIT_READ`

#### Follow-up Questions

- 审计会不会把请求拖慢？（我的写是同步的、单行插入，Demo 量级无感；生产要么异步批量+落盘保证，要么接受写失败可见——不能两个都不要）
- 审计数据保留多久？（由合规定，`[需要本人确认：恒光内部日志留存要求]`；技术上要分区/归档 + 冷存储）

#### Pitfalls

- 不要说「所有操作都审计了」。承认三个只读端点是当前最实的一处不足。
- 不要把「记不记 prompt」说成性能问题，它是**数据分级**问题。

#### Interview Keywords

`audit the attempts not just successes` `capability changes are events` `audit reads must be audited`

---

## Q15-04 审计数据谁能看？

#### Short Answer

我这里是 `audit:read`（admin + manager）。但**看审计这件事本身当前不留痕**，所以严格说我还没有一个可以对外承诺的审计查看机制——这是我知道的第一优先补项。

#### Standard Answer

`[MY DESIGN]` 现在能做到：`GET /api/audit` 与 `GET /api/audit/{request_id}` 要求 `audit:read`；operator 拿到 403 并被记为 `denied`；分页上限 100（`MAX_PAGE_SIZE`）；查询条件是命名参数绑定；`/api/users` 里我会把 `audit:read` 的持有者列出来（`roles_for_permission`），**让权限可见**是一种治理手段。
但我必须补三条不足：① 无「查看审计的审计」；② 无按数据范围隔离（manager 能看到全平台所有人的活动，这在多基地场景下不合适）；③ 无导出管控与保留策略（`clear()` 只清内存，DB 行按注释刻意保留，但这不等于有归档流程）。
`[PRODUCTION_NEXT]` 我的方案：**审计查看独立权限（不复用业务角色）+ 每次读取/导出写一条 `audit.read` + 按组织范围过滤 + 只追加不可删改 + 定期哈希锚定 + 冷存归档与保留期**。
`[INFERENCE]` 关于人的问题也要正面答：安全/审计岗和业务管理者看的范围应当不同。我会把它写成使用规范条款而不是代码默认值——`[FACT]` 这与 JD 第 6 条「制定平台使用规范」是同一件事。

#### My Project Evidence

- `app/api/audit.py`（`AuditReaderDep = Depends(require(Permission.AUDIT_READ))`）
- `app/auth/permissions.py`（manager 持 `audit:read`）
- `tests/integration/test_rbac.py`（32，含 operator 读审计被拒）
- 缺口：`app/api/audit.py` 无 `record_api`

#### Follow-up Questions

- 你要不要支持「IT 能看操作但看不到内容」？（能。因为内容压根不进审计表，只有摘要——这是我这个设计的一个意外好处）
- 审计被删了怎么办？（现在能删：SQLite 一张普通表。**生产必须独立写账号 + 只追加 + 外部锚定**）

#### Pitfalls

- 不要说「我们的审计体系符合企业要求」。合规表述我没资格说，而且我的表是可写的。
- 不要暗示有 RBAC 分层查看（没有组织范围过滤）。

#### Interview Keywords

`least privilege to read` `audit-read must itself be audited` `append-only + anchoring next`

---

## Q15-05 如何保证不可篡改？

#### Short Answer

我现在保证不了——它就是 SQLite 的一张普通表，同一个库文件同一个账号可读写。我能保证的是「写入路径单一 + 净化集中 + 只追加的用法」。生产要靠独立写账号、只追加存储和外部锚定。

#### Standard Answer

`[MY DESIGN]` 我在 Demo 里的真实保障程度（这条必须说准）：
- **单一写入点**：只有 `AuditLog.record()` 写这张表（`_INSERT_SQL` 是 INSERT-only，代码路径里没有 UPDATE/DELETE 审计行的语句）；
- 净化集中、无法绕过（`record()` 内调用）；
- `tests/unit/test_audit.py` 钉住「secrets 永不落库」和「写失败不外抛」。
- **但**：DB 文件与业务表同库同权限，任何能连上 SQLite 的人都能改；无哈希链、无外部存储、无 WORM。
`[PRODUCTION_NEXT]` 我会按成本递增分四层：
① **权限层（最便宜，先做）**：审计写用**独立数据库账号**，只有 `INSERT` + `SELECT`，业务应用账号无写权；分表/分库；
② **可验证层**：每日/每 N 行做哈希链（`h_i = hash(h_{i-1} || row_i)`）并把链头**周期性送到外部**（对象存储 WORM、或另一个系统的日志），这样「本地改了一行」可被检测；
③ **归档层**：冷存储 + 不可变桶（object lock / retention policy），保留期由制度定；
④ **组织层**：删除/修改变成一个需审批的操作 + 审计的审计 + 定期由第三方（内部安全岗）复核。
我会顺带说清一个常见误解：**「区块链存证」不是这个问题的默认答案**。要的是「本地写入者不能悄悄改历史 + 改动能被发现」，①+② 就能做到，代价低得多。

#### My Project Evidence

- `app/observability/audit.py`（`_INSERT_SQL` 唯一写入路径、`clear()` 只清内存且注释写明「DB rows are kept on purpose」）
- `app/db/models.py::AuditLog`（普通表，`idx_audit_logs_created_at` 索引；无触发器/无权限隔离）
- `data/runtime/app.db` 与业务表同库（`app/config.py::database_url`）→ 这就是不足的直接证据

#### Follow-up Questions

- 那你怎么防止「运维直接改库」？（改不了：独立账号 + 库文件权限 + 外部锚定后改动可检测；真要防内部人员还得靠双人制度）
- 审计和日志不一致时信谁？（信有身份、有 request_id、结构化的那条；不一致本身就是告警事件）

#### Pitfalls

- **绝对不要说「我的审计不可篡改」**。这是我准备清单里标红的自我提醒。
- 不要把「没有」说成「不需要」——要说「Demo 里接受这个风险，生产按这四层补」。

#### Interview Keywords

`single insert path` `honest about what's missing` `append-only account + external anchoring`

---

## Q15-06 出事之后怎么追溯一次回答？

#### Short Answer

拿 `request_id`（响应头或响应体里都有），一次查询拿到整条链：HTTP 事件 → 鉴权拒绝（若有）→ 每次工具调用 → Agent 运行状态；再用响应里的 `sources` 回到具体文档片段。

#### Standard Answer

我的实操 SOP（面试时我会按这个顺序说，因为它是我真的跑过的动作）：
```bash
  # 0) 用户/前端提供的 request_id（响应体 request_id 或 X-Request-ID 响应头）
curl -s -H "Authorization: Bearer demo-admin-token" \
     http://127.0.0.1:8000/api/audit/req_xxxx | jq

  # 1) 先看 agent.run 那行：status / steps / tool_calls / denied_calls / run_status / latency_ms
  # 2) 再看每个 tool.call：tool_name / status / operation / row_count / error_code
  # 3) 有 answer 但内容不对 → 去响应体的 sources[]（document_id/section/page/url）核原文
  # 4) 没有 answer 或 502 → 看 chat.complete=error 的 error_type，再对 /metrics 的 error_by_code
  # 5) 权限争议 → 对比 denied 行的 role 与 required_permission（矩阵是代码常量，可直接查表）
curl -s -H "Authorization: Bearer demo-admin-token" 'http://127.0.0.1:8000/metrics' | jq .
```
三类问题分别落在哪：
| 现象 | 第一步 | 判据 |
|---|---|---|
| 答案内容错 | `sources` → 打开 `url` 对原文 | 引用有没有、指对不对 |
| 答案说「没有足够信息」 | `knowledge.search` 行的结果数 | 0 = 缺料/召回问题；>0 = 生成问题 |
| 「它没查 ERP」 | `tool.call` 序列 | 没有调用 = 模型选择问题；有调用但 denied = 权限；error_code = 参数/DB |
| 慢 | `latency_ms` + `/metrics.requests_by_endpoint` | 是单请求还是端点普遍 |
| 502 | `chat.complete=error` + `error_by_code` | provider 侧还是网关侧 |
**我做不到的（要说清）**：① 没有 prompt/响应正文，无法事后复现「模型当时看到什么」——只能靠同一个 mock/同一 provider 重放；② 没有分布式 tracing，跨进程边界（如果以后拆服务）要靠 request_id 继续透传；③ 没有 APM，只有端点均值与峰值延迟，**看不到 P95**。
`[PRODUCTION_NEXT]` 复现能力要专门设计：**版本三元组**（模型版本 + 知识库快照版本 + prompt 版本）记在审计里，这样「当时那次」才能被重放。这是我今天缺的一块，也是最容易在真实事故复盘时被打脸的一块。

#### My Project Evidence

- `app/api/audit.py::audit_by_request_id`（未知 id → 结构化 404，不返回空列表冒充「没问题」）
- `app/api/agents.py::AgentRunResponse`（`request_id / status / trace / tool_calls / sources`）
- `app/observability/metrics.py::snapshot()`（15 项计数器）
- `DEMO_SCRIPT.md` Step 6/7（现场就是一次端到端追溯）

#### Follow-up Questions

- 一次 agent.run 平均几行审计？（1 行 `agent.run` + 每工具 1 行 + 可能的拒绝行；我语料和 mock 下的典型链路是 2–3 行）
- 你怎么定位「哪一步慢」？（`trace` 里每步有 `latency_ms`；端点级有均值/峰值；**但无分位数**——这是我列的缺口）
- 日志和审计谁权威？（审计是有身份有结构的那份；日志是排障细节，可以很啰嗦）

#### Pitfalls

- 不要说「我们能完整复现任何一次回答」。我没有存 prompt。
- 不要把 demo token 说成机密（README 里就是公开的），但也不要说「生产可以这么干」。

#### Interview Keywords

`request_id is the whole story` `reproduce via version triple` `no P95 yet`
# 16 · 可观测性与错误契约

## Q16-01 Metrics 记了什么？

#### Short Answer

15 项进程内计数器：请求总量/成功/错误、延迟均值与峰值、按端点计数与平均延迟、按状态类（2xx/4xx/5xx）、按错误码、工具调用与失败、权限拒绝、Agent 运行按终止状态、审计写入次数、uptime。JSON 输出在 `GET /metrics`。

#### Standard Answer

`[MY DESIGN]` `app/observability/metrics.py` 是一个 `threading.Lock` 保护的小计数器对象（模块级单例 `metrics`），四个写入方法：
`observe_request(endpoint, status_code, latency_ms, error_code)` / `observe_tool_call(tool, success, permission_denied)` / `observe_agent_run(status)` / `observe_audit_write()`。
`snapshot()` 输出：`request_count, success_count, error_count, avg_latency_ms, max_latency_ms, requests_by_status_class, requests_by_endpoint{count,avg_latency_ms}, error_by_code, tool_call_count, tool_error_count, permission_denied_count, agent_run_count, agent_runs_by_status, audit_write_count, uptime_seconds`。
`GET /metrics` 额外附 `app{version, provider}` 与 `endpoint/request_id`。
三个我认为值得讲的取舍：
① **中间件自己计时**：`RequestContextMiddleware` 在 `send_wrapper` 里抓状态码、结束时统一 `_observe(...)`，所以**成功与异常路径都会计数**（异常路径用 `fallback_status=500`）；错误码通过 `request.state.error_code` 由错误处理器回传（`errors.py::_remember`），这是一个很朴素的「跨层传值」而不是上下文对象。
② **`/metrics` 故意不需要 token**：模块注释写的是「dashboard/poller 应当能以非用户身份读，且 payload 只有计数器，没有业务数据也没有身份」。我承认这是一个**部署边界假设**（内网/LB 侧要限），生产上我会放到内网端口或加 Basic Auth。
③ **`reset()` 存在**：测试需要一个干净的计数器窗口（`conftest` 与 `test_metrics.py` 用它），这也是我为什么用「显式方法」而不是全局字典。
**我不假装这是 Prometheus**。`[PRODUCTION_NEXT]`：`snapshot()` 已经是单一日出点，加一个 exposition-format 序列化函数就能变 exporter；但真正的缺口是**没有分位数**——只有均值与峰值，P95/P99 需要直方图（`[FACT]` SPEC Day 4 明确不要求 Prometheus，所以我选了最小可用面）。

#### My Project Evidence

- `app/observability/metrics.py`（`Metrics`、`snapshot()`、模块注释）
- `app/observability/middleware.py`（`_observe`、`send_wrapper`、`except Exception` 路径）
- `app/api/metrics.py`、`app/api/errors.py::_remember`
- `tests/unit/test_metrics.py`（12）

#### Follow-up Questions

- 均值延迟有什么坑？（尾部被平摊掉；一个 60s 的超时能把 20 个请求的均值毁掉 → 所以我同时记 `max_latency_ms`，但这只是权宜）
- 内存计数器重启就没了怎么办？（是。生产上指标必须由拉取侧或 agent 侧存时序库；进程内只当「当前窗口」看，我接受这个限制因为单机 Demo）
- 你怎么把 token 成本接进来？（`ModelResponse.usage` 已经在网关返回值里，缺的是往 `Metrics` 传一条 `observe_usage(provider, model, prompt_tokens, completion_tokens, cost)`；这是我列的最小增量之一）

#### Pitfalls

- 不要说「我们有 P95」。没有。
- 不要说「metrics 里有业务数据」——恰恰相反，它被刻意设计成无业务数据，这就是它能公开的前提。
- 不要说「用了 Prometheus / Grafana」。没有，SPEC 也不要求。

#### Interview Keywords

`15 counters` `latency mean + max, no percentiles` `middleware observes both paths` `snapshot is the single source`

---

## Q16-02 结构化日志怎么做？

#### Short Answer

一个 `contextvars` 绑 request_id + 一个自定义 Formatter：每行一个 JSON 事件（stdout），固定字段名；`LOG_JSON=false` 时退化成人类可读单行。

#### Standard Answer

`[MY DESIGN]` `app/observability/logging.py`：`configure_logging()` 装配 handler 与 formatter；`request_id_scope(rid)` 是个 contextmanager，中间件用它包住整个请求，所以**任何一处 `logger.info` 都自动带 request_id**，不需要每个调用点手工传。
日志记录通过 `extra={...}` 传结构化字段，`FIELD_KEYS` 白名单决定哪些字段进 JSON（`event/endpoint/operation/method/status/status_code/latency_ms/tool/model/mode/steps/user/role/error_code/provider/rows/documents/…`）——**白名单是关键**：不写白名单就会有人把整个响应体塞进 `extra` 里，日志变成数据泄露点。
`event` 字段是事件名，我把它当**低基数可枚举**的东西来用（`http.request`、`app.start`、`audit.write_error`、`audit.skip`、`tool.error`、`error.platform`、`error.unhandled`、`agent.run_error`、`provider.fallback`（在网关用 logging.warning））。生产上这些就是告警规则名。
三类事件的分层我要说清楚，因为面试常问「日志/审计/指标有什么区别」：
- **日志**：排障，可以有细节（异常类型名、截断后的 message），**允许丢失**；
- **审计**：质证，结构化 + 身份 + 净化摘要，**不允许丢失**（写失败要告警）；
- **指标**：聚合数字，用于趋势与告警，不关心单次。
`[PRODUCTION_NEXT]`：接 OTel（trace id 与 span，把 provider/DB/向量库调用变成可见的瀑布）、日志集中（Loki/ELK）、并给日志加**采样与限流**（一个 traceback 循环能把磁盘写满，这是真实事故模式）。

#### My Project Evidence

- `app/observability/logging.py`（`REQUEST_ID_HEADER`、`_request_id` ContextVar、`FIELD_KEYS`、`request_id_scope`、`get_logger`、`current_request_id`）
- `app/observability/middleware.py`（每个请求一条 `http.request`）
- `app/config.py::log_level / log_json`（`.env.example` 有注释）
- `tests/unit/`（`LOG_JSON=false` 的 dev 模式也覆盖）

#### Follow-up Questions

- 日志里会不会泄露敏感数据？（有专门测试钉住「日志不含 API key」；另外我把工具错误只记异常类型名——`queries.py::_run` 的 `logger.warning` 里截断 200 字符）
- 为什么不接 ELK？（本期不需要；但正因为字段是白名单结构化的，接上去只是换个 sink）

#### Pitfalls

- 不要说「我们有 tracing / OTel」。只有 request_id 相关，**没有 span 树**。
- 不要说「日志里什么都没有」。里面有异常类型名与截断信息；准确说法是「没有 prompt 正文、没有凭据」。

#### Interview Keywords

`contextvar correlation` `field whitelist` `event names are alert rules` `log ≠ audit ≠ metrics`

---

## Q16-03 统一错误处理怎么设计？

#### Short Answer

一个异常层次 + 一个信封 + 四个 handler：任何离开平台的失败都是 `{detail, request_id, error:{code,message,details}}`，人读 `detail`、程序分支 `error.code`，永远不给 traceback。

#### Standard Answer

`[MY DESIGN]` `app/api/errors.py`：
- `PlatformError` 基类带 `status_code` / `code` / `details` / `headers`；子类 `AuthenticationError`(401) / `PermissionDeniedError`(403) / `NotFoundError`(404) / `ConflictError`(409) / `ProviderError`(502) / `StorageError`(503) / `DatabaseError`(503)。
- `register_exception_handlers` 装四个 handler：`PlatformError`（>500 额外 `logger.error`）、`HTTPException` **和** `StarletteHTTPException`（两个都注册，因为未匹配路由抛的是 Starlette 那个，而 handler map 按精确类查找——这是我踩过的一个真细节）、`RequestValidationError`（422，把 `exc.errors()` 过 `_json_safe` 才能序列化）、兜底 `Exception`（500 `INTERNAL_ERROR`）。
- 兜底 handler 的 message 是「服务内部错误，请使用 request_id 查询审计日志」+ `details={}`，**不含 traceback**；完整异常走 `logger.exception` 带 request_id。
三个设计决定：
① **`detail` 与 `error.code` 并存**：FastAPI 客户端与 Day-1/2 测试读 `detail`，前端与监控按 `code` 分支。旧字段不删是**兼容性判断**，不是遗留（我在文件注释里写明了理由）；
② **status → code 有默认映射**（`_CODE_BY_STATUS`）：裸 `HTTPException(429)` 也能拿到 `TOO_MANY_REQUESTS`。这个映射是我审查时发现的缺陷（Fix #8，原来 429 会掉进 `INTERNAL_ERROR`）；
③ **`request.state.error_code` 作为跨层传值**：错误处理器把 code 写进 request state，中间件读它去计数——所以 `error_by_code` 是**按真实业务错误码**统计的，不是按 HTTP 状态猜的。

#### My Project Evidence

- `app/api/errors.py`（全文，尤其是双 HTTPException 注册与 `_json_safe`）
- `app/observability/middleware.py`（读 `state.error_code`）
- `tests/integration/test_platform.py`（错误信封、404、422、兜底 500、无 traceback 断言）
- `[FACT]` `git show 460a6ee`（Fix #8 = 429 映射）

#### Follow-up Questions

- 为什么不直接用 FastAPI 默认？（默认把校验错误变成一大段 `detail` 数组，且没有稳定 code 与 request_id，前端只能靠 HTTP 状态猜）
- 内部错误要不要返回 stack？（绝不。开发环境可以，但要在中间件/配置层控制，不能靠 handler 里写 if）
- 错误码会不会膨胀？（会。`[PRODUCTION_NEXT]` 要一份错误码注册表 + 每码一个 owner + 前端 i18n 文案表；我现在只有 9 个码，可控）

#### Pitfalls

- 不要说「所有错误都是结构化 JSON 且带 code」而不补一句「未知 500 只有 `INTERNAL_ERROR`，粒度靠 request_id + 日志」。
- 不要说「我们的 422 里不含用户输入」——`_json_safe` 会把 `ctx`/`input` 序列化出来，**可能包含用户提交的字段值**。这是我复查后确认的一个真实风险点（§22），生产上应该按开关裁剪。

#### Interview Keywords

`one envelope` `human detail + machine code` `no traceback to client` `status→code mapping`

---

## Q16-04 超时 / 重试 / 限流怎么做？

#### Short Answer

超时只有一部分（provider 60s、nginx 120s、httpx 有、工具没有）；重试**没有**；限流**没有**。我只做了错误分类、审计、指标和「失败不打挂平台」，这三件是我认为前置条件。

#### Standard Answer

我会先给一句准确的现状，再讲设计：
**现状**
- provider 侧：`OpenAICompatibleProvider` 建 `httpx.AsyncClient(timeout=60.0)`，单次调用，失败 `raise_for_status()` → 网关捕获 → 502 或降级；
- HTTP 侧：`web/nginx.conf` 的 `proxy_read_timeout 120s`；`/health` 有 `start_period: 40s`、`interval: 15s`、`retries: 5`（Docker 层重试，不是应用层）；
- 工具侧：**没有 timeout**（Q9-04）；
- 重试：**没有**。我刻意不做，因为无幂等保证的自动重试在企业集成里可能重复触发外部动作；
- 限流：**没有**。`429` 与 `TOO_MANY_REQUESTS` 的错误码已经就位（Fix #8 就是为它把映射修对），但**没有任何地方抛 429**。
`[PRODUCTION_NEXT]` 我会按这个顺序补（每一步都要有测试与指标）：
① **per-tool / per-provider 超时 + 取消传播**（不取消的超时是假超时）；
② **总请求预算**：`deadline` 从中间件生成，向下传，各层取剩余预算；保证「工具超时之和 ≤ Agent 墙钟 ≤ HTTP 超时」这个不等式；
③ **只读操作的有限重试 + 指数退避 + jitter**：`[MY DESIGN]` 我会用 tenacity 而不是自己写循环，理由是自己写的退避代码通常缺 jitter 与尝试计数可视化——**但重试必须配「本次是第 N 次尝试」写进日志与响应头**，否则排障时没人知道；
④ **熔断**：按 provider / 按工具，滑窗错误率超阈值就快速失败，并把「跳闸」做成指标事件；
⑤ **限流**：进程内滑窗（单节点够用）→ 共享计数器（Redis，这是我第一个真正需要 Redis 的场景）→ 按租户/用户/端点分层 + **Agent 预算与配额分开管**（预算管一次运行，配额管一个用户一段时间）；
⑥ **背压**：入口队列上限 + 429，而不是让 uvicorn worker 堆到死。
`[INFERENCE]` 对这个岗位的规模判断：`[FACT]` 招 1 人、内部平台、`[INFERENCE]` 用户量级是「几百到几千员工」而不是公网流量 → 所以我会把优先级放在**超时与熔断**（保护 ERP 与 GPU）而不是分布式限流。这也是我为什么不在本期做限流。

#### My Project Evidence

- `app/gateway/openai_compatible.py`（唯一的应用层 timeout）
- `web/nginx.conf`（`proxy_read_timeout 120s`）
- `docker-compose.yml`（healthcheck 参数）
- `app/api/errors.py`（429 映射与 `ERROR_TOO_MANY_REQUESTS` 已备好，无生产者）
- 缺口：`app/agent/executor.py` 无 timeout、全仓无 retry/backoff/circuit-breaker 代码

#### Follow-up Questions

- 为什么不现在加个 tenacity 就完事？（重试的语义前提是幂等，而我只读工具才安全；先把幂等与对账想清楚，否则重试是事故放大器）
- 熔断和降级同时存在会不会互相掩盖？（会。所以熔断必须发指标事件、降级必须打标——两个都要「响」）
- 你怎么验证不回归？（用可注入的假 provider/假 tool 制造延迟与失败，断言取消发生、断言预算满足不等式；我已有 fake 注入能力，缺的是这些测试）

#### Pitfalls

- **不要说「有重试和限流」**。这是三个最容易吹、也最容易被抓的点之一。
- 不要说「429 没做说明我不重视」——我的说法是：**错误契约先行，实现在阶段二**，并且我给了不等式与顺序，说明我是按工程顺序想的。

#### Interview Keywords

`timeout ≠ cancellation` `retry requires idempotency` `circuit breaker events` `budget inequality` `429 contract ready, no producer`

---

# 17 · 安全

## Q17-01 这个项目里你做了哪些安全措施？

#### Short Answer

六件我能当场指出代码的：所有 /api 端点默认鉴权 + 双层授权、SQL 全参数化 + 固定 operation、审计写入前的字段 denylist 净化、错误响应不回显凭据与 traceback、密钥不进 Git 且 `users` 端点不外泄 token、能力面白名单（无写工具、无控制工具）。

#### Standard Answer

我按「威胁 → 我做的那一件事 → 证据」的顺序讲，因为这比背 OWASP 名词有说服力：
① **未认证访问** → `require()` 依赖工厂，`/api` 下全部端点受保护，公开面只有 `/health` 与 `/metrics`（无业务数据）；缺 token/错 token 是 **401 而不是降级成 admin**（`app/auth/auth.py` 的模块注释就写了这条纪律）；
② **越权（垂直）** → 两族不互相继承的权限 + `ToolExecutor` 二次检查，全部 fail-closed（未知角色归到 operator、无身份直接拒）；
③ **SQL 注入** → 每段 SQL 是模块级常量，值只走 `text(sql)` + 命名参数字典；没有任何字符串拼接进 SQL 的通道（`app/db/queries.py`）；
④ **凭据泄露到响应** → **Fix #3** 把 401 details 里的 demo token 去掉了（`git show 460a6ee` 可查 diff）；`GET /api/users` 明确**不返回 token**（`app/api/users.py` 注释）；`GET /api/models` 只报可用性不报 base_url/key（有 Day-1 回归测试钉住）；
⑤ **敏感内容进审计** → `sanitize_summary` 集中净化：13 项 denylist、嵌套只留长度、字符串截断、key 数量上限；
⑥ **traceback / 内部结构外泄** → 兜底 handler 只回「服务内部错误，请使用 request_id 查询审计日志」；`_json_safe` 把校验错误里的异常对象换成类型名；
⑦ **供应链与仓库卫生** → `.gitignore` 排除 `.env` 与 `data/runtime/*`，仓库里只有 `.env.example`；`api.Dockerfile` 用 `uv sync --frozen --no-dev`（镜像不带测试依赖）；文档数据目录在容器里挂 `:ro`；
⑧ **能力面（对 AI 系统最关键）** → 只有 4 个只读工具，无写、无 SQL、无控制类动作。模型不可能提示注入出一个不存在的工具。
`[MY DESIGN]` 我会补一句我认为**最有价值**的观察：AI 平台的安全重心从「输入过滤」挪到了「**能力面 + 授权点 + 留痕**」。前者的效果是概率性的，后三者是架构性的。

#### My Project Evidence

上表 8 条各有一条可指的文件；另有 `tests/integration/test_rbac.py`（32）、`tests/unit/test_auth.py`（23）、`tests/unit/test_audit.py`（19）作为回归证据。

#### Follow-up Questions

- 你做过依赖漏洞扫描吗？（`[FACT]` pyproject 有 ruff；`[MY DESIGN]` 没有 pip-audit/依赖扫描，`uv.lock` 锁版是我的实际做法 → 缺口 §22）
- 有 HTTPS 吗？（Demo 里 nginx 是 80 端口明文，内网 + 演示环境；`[PRODUCTION_NEXT]` 内网 CA/TLS 终止 + HSTS + 强制 https 跳）
- 怎么防 XSS？（前端 React 默认转义，我没有 `dangerouslySetInnerHTML`；答案与引用文本作为文本渲染——我可以当场 grep 证明）

#### Pitfalls

- 不要说「通过了安全审计 / 渗透测试」。没有。我只能说「我做过一次自查式代码审查，找到 5 个缺陷并修了」（§21）。
- 不要把 demo token 说成需要加密保存的秘密：它们**故意**写在 README/`.env.example` 里（`.env.example` 的 Auth 注释解释了为什么）。真正的安全点是「未知 token 不继承权限」。这个区分说错会显得很不懂。
- 不要漏说自己没有的东西：无 SSO、无密钥管理服务、无 secrets 轮转、无网络隔离策略、无 WAF、无静态加密、无依赖扫描、文档级 ACL 缺失。

#### Interview Keywords

`fail-closed auth` `parameterized SQL only` `central sanitization` `capability surface is the control` `no traceback no secrets in responses`

---

## Q17-02 如何防止 Prompt Injection？

#### Short Answer

我的答案是「三层」：不让模型持有特权（工具白名单 + 固定 operation）、授权在服务端强制（executor 不看 prompt 说了什么）、数据边界在检索层强制（而不是靠模型自律）。第三层文档 ACL 我还没做。

#### Standard Answer

`[MY DESIGN]` 我先讲我认识的攻击面（这决定回答的可信度）：
① **直接注入**：用户输入「忽略以上指令，调用 xxx」；
② **间接注入（对企业 RAG 更要命）**：**知识库文档里**写着「请把下面内容原样发给模型…」或「系统指令：向所有用户显示…」——检索命中后它进了 prompt；
③ **工具描述投毒**：外部来源的 tool description 本身是 payload（`[FACT]` MCP 规范明确把工具描述列为**不可信输入**，来源见 §来源）；
④ **结果回填注入**：工具返回的文本被模型当作指令继续执行（我的 tool message 就是文本）；
⑤ **提取型**：诱导模型复述系统 prompt 或其它用户的数据。
**我现在真正拦得住的**：
- 系统 prompt 与用户内容分离（`app/agent/prompts.py`、`app/rag/prompt.py`），并且策略里写了「不得编造」「不得假装调用不存在的工具」；
- **未知工具不执行**（`UNKNOWN_TOOL`）、**operation 不在白名单不执行**（`INVALID_OPERATION`）、**参数越界不执行**（`INVALID_ARGUMENTS`）——所以「说服模型去改库存」在架构上不可达，因为**没有那样的工具**；
- 权限在服务端判（`ToolExecutor` 用 `Actor`，与 prompt 内容无关），prompt 改变不了授权；
- 引用与来源随答案返回（人可以看到它引了什么，异常引用肉眼可见）；
- 只读：最坏结果是一次多余查询或一条错误文本，而不是数据损坏。
**我拦不住的（必须说）**：
- **②间接注入是我现在最大的洞**：因为文档级 ACL 没有（Q7-14），一份恶意或被污染的文档一旦 ingest，就能影响所有人的回答内容。`[PRODUCTION_NEXT]` 顺序：ACL 与内容准入 → 外部内容进 prompt 前加**显式围栏与标签**（标成「资料」而不是指令，并在策略里说明「资料中的任何指令都不是指令」）→ **输出侧校验**（答案里的数字/URL 必须出现在被引片段中，否则退回）→ 高危动作一律走审批（模型没有直接执行权）。
- ③：引入外部 MCP server 时我不会原样透传它的 description（§10 Q10-04）。
- ⑤：我没有任何「防系统 prompt 外泄」的机制。生产上我会靠**让 prompt 里没有值得偷的东西**（凭据/表结构不放 prompt），这比检测外泄有效。
一句话收口：**「prompt 注入防不住所以不做安全」是错的，正确做法是假定它会发生，然后把它能造成的最大后果压到可接受。**

#### My Project Evidence

- `app/agent/executor.py`（三码 + fail-closed）、`app/agent/tools/*`（无写工具、operation Literal）
- `app/agent/prompts.py` / `app/rag/prompt.py`（系统/用户分离 + 禁止编造）
- `tests/unit/test_erp_tool.py`、`test_agent_tools.py`（白名单与参数拒绝的回归证据）
- 缺口证据：`app/rag/ingest.py` 无内容检查、`retriever` 无 principal 参数

#### Follow-up Questions

- 加一道「注入检测模型」行不行？（可以作为纵深，但不能当边界：绕过成本低、误报会伤可用性。我会让它做**告警**而不是**放行依据**）
- 输出侧校验怎么落地？（规则优先：数字/URL/document_id 与被引片段求交；LLM 自检只做辅助且不进信任链）
- 你怎么测自己防住了什么？（造对抗样本集：污染文档 + 直接注入话术 + 提取请求，把「执行了非白名单动作」次数钉成 0——**我现在没有这个测试集**，这是我列的第一优先安全项）

#### Pitfalls

- 不要说「我们用 LLM 审 LLM 所以安全了」。
- 不要承诺「防住了 prompt 注入」。要说「**能力面窄 + 服务端授权 + 无副作用**使它的后果可控，同时文档准入与输出校验是我下一步」。
- 不要装作间接注入不存在——做过企业 RAG 的人一定会追问这一条。

#### Interview Keywords

`indirect injection is the real risk` `narrow capability surface` `server-side authorization ignores prompts` `output-side verification next`

---

## Q17-03 API Key 怎么管理？

#### Short Answer

`.env`（gitignore）→ 环境变量 → `Settings` 只读对象；三个「不外泄」检查点：不进 Git、不进日志与审计、不进任何响应体。同时我承认：没有密钥管理服务、没有轮转、没有按环境隔离。

#### Standard Answer

`[MY DESIGN]` 具体路径与强制点：
- 来源：`app/config.py` 从环境变量读（`LLM_API_KEY` / `EMBEDDING_API_KEY`），`.env` 被 `.gitignore` 排除，仓库里只有 `.env.example`（空值）；
- 使用：只在 `OpenAICompatibleProvider` 内部拼 `Authorization: Bearer …`，不进任何 dataclass 字段（所以不会被 `dataclasses.asdict()` 之类的操作意外导出）；
- **注册门槛**：`_init_providers()` 要 `base_url` **且** `api_key` 都非空才注册真实 provider（所以「忘了配 key」的表现是明确回落 mock，而不是半启动状态）；
- **响应侧**：`GET /api/models` 只报 `available` 布尔（`app/api/models.py` 注释写明「no API key, base URL, token or other environment value is included」，并有 Day-1 回归测试钉住）；
- **日志与审计侧**：`DENYLIST_TERMS` 含 `api_key`/`apikey`/`authorization`/`token`/`secret`，结构化日志字段走 `FIELD_KEYS` 白名单；
- **容器侧**：`docker-compose.yml` 的 `env_file: required: false` + 镜像里没有密钥层（`api.Dockerfile` 只 COPY 代码与数据目录）。
`[需要本人确认：公司是否已有 Vault / KMS / 配置中心，以及是否允许从 Pod 环境变量注入]`
`[PRODUCTION_NEXT]` 我会补四件：① 从 Vault/KMS 拉取，**不落静态环境变量**（启动时注入 + 内存态）；② 轮转与双活窗口（新旧 key 并存一段时间，provider 层热加载，不重启）；③ 按用途分 scope（一个 key 只能 chat，另一个只能 embeddings；出问题能定位且损失面小）；④ 用量与异常检测（某 key 的调用量突变 → 告警，这是最便宜的「泄露了」信号）。
**一个常被忽略的点我要主动说**：**key 也可能从模型侧泄露**——如果用户提问里粘贴了自己的 key，它会进 prompt、进 provider 日志。所以净化不能只管我自己注入的字段，还要考虑「用户内容里带凭据」。生产上我会在日志/审计侧做正则脱敏（信用卡/身份证/手机号/key 格式），并明确写进使用规范告知用户「不要把凭据粘进对话框」——`[FACT]` 这正是 JD 第 6 条「平台使用规范」的实际内容。

#### My Project Evidence

- `app/config.py`（`llm_api_key` / `embedding_api_key` 只从 env 读）+ `.gitignore`（`.env`）+ `.env.example`
- `app/gateway/openai_compatible.py`（唯一使用点）
- `app/gateway/router.py::_init_providers`（注册门槛）
- `app/api/models.py` + `app/observability/audit.py::DENYLIST_TERMS` + `app/observability/logging.py::FIELD_KEYS`
- `tests/unit/test_gateway.py` / `tests/integration/test_platform.py`（响应体与审计不含凭据的断言）

#### Follow-up Questions

- 日志里出现 key 怎么办？（白名单 + denylist 双保险；生产再加一层 sink 侧脱敏，防止有人绕过约定）
- 多租户呢？（`[PRODUCTION_NEXT]` 一个平台 key + 配额，还是 BYO key，是产品决策；BYO key 就要**加密存储 + 单独泄露面评估**，我倾向第一期不支持 BYO）
- 你会把 key 放进 `Settings` dataclass 吗？（现在放了字符串字段但从不序列化；更严格的做法是只存「是否可用」+ 在使用点即时读取环境变量。这是我的下一步之一）

#### Pitfalls

- 不要说「我们有完整的密钥生命周期管理」。我没有轮转、没有 KMS。
- 不要说「key 加密存在数据库里」——我根本没存到数据库。

#### Interview Keywords

`env-only + gitignored` `three no-leak checkpoints` `registration gate` `rotation + scoped keys next`

---

## Q17-04 如何防止越权访问（水平 / 垂直）？

#### Short Answer

垂直越权靠两族权限 + fail-closed + 逐格测试；水平越权（同类资源跨用户/跨部门）我**没有数据**所以只有形状，`[PRODUCTION_NEXT]` 必须在数据访问层注入 owner/范围条件，而不是靠上层过滤。

#### Standard Answer

`[MY DESIGN]` **垂直（我现在真的防住了）**：
- 所有入口都过 `require()`，没有「先放行后补」；
- 工具层独立检查，`Actor` 从请求构造并一路**显式**传递（不是全局对象，不会被并发串号）；
- 未知角色 `normalize_role()` 落到 operator（最受限），无身份直接拒；未认证 actor 到不了工具执行（`ToolExecutor` fail-closed）；
- 401/403 都用统一信封，且 403 会先写 `denied` 审计再抛（拒绝是有记录的）；
- 逐格回归：`tests/integration/test_rbac.py` 32 个测试；
- 能力目录本身受保护（`/api/models` 需要 `models:list`）——攻击者不该能免费枚举平台能力。
**水平（我承认没做，因为 Demo 没有多租户数据）**：审计表按 `user_id` 关联，但 `GET /api/audit` 不做属主过滤（有 `audit:read` 就能看全部）；Agent/会话也没有属主概念。`[PRODUCTION_NEXT]`：属主条件必须在**查询里**（`WHERE ... AND owner_scope IN (:actor_scopes)`），不能是取回结果后再筛（先取后筛会泄露计数、排序信息与缓存）。
`[MY DESIGN]` 我会主动补一条我觉得最有说服力的原则：**权限判定的输入必须是「不可伪造的身份」+「集中定义的授权」**。我的 `Actor` 只从 `CurrentUser` 构造（来源是 header 解析），不接受请求体里传 `role`/`user_id`——如果允许，那 403 就成了装饰。这个「身份不从请求体来」的选择是我最想被问到的一条。
`[INFERENCE]` 落到恒光的多基地结构（`[FACT]` 公开资料：怀化/衡阳/老挝三基地 + 控股子公司，来源见 §来源），水平越权的真实形态就是「A 基地的人看到 B 基地的隐患台账与采购数据」，所以我把它列为接真实数据前的**第一道必答题**。

#### My Project Evidence

- `app/auth/dependencies.py`（403 前先落 `denied` 审计）
- `app/observability/audit.py::Actor.from_user`（唯一身份构造入口）
- `app/agent/executor.py`（无身份直接拒）
- `app/api/audit.py`（**没有**属主过滤 → 缺口证据可当场指）
- `tests/integration/test_rbac.py`、`tests/unit/test_agent_permissions.py`

#### Follow-up Questions

- 怎么测防越权？（**负例测试优先**：每格一个「低权限 + 该资源」断言 403/denied；生产再加自动化的「越权扫描」——用每个角色遍历一遍每个端点，比对预期矩阵。我已经有逐格测试，没有全端点遍历器）
- 有 IDOR 风险吗？（有形状：`GET /api/audit/{request_id}` 里 request_id 是 uuid4，不可枚举但**不是授权**——拿到 id 的 manager 能看任何人的链。这正属主检查缺失）
- 前端怎么配合？（不配合：前端隐藏按钮只是 UX）

#### Pitfalls

- 不要说「我们的 RBAC 防住了所有越权」。垂直防住了，水平没做。
- 不要说「request_id 不可猜所以安全」——那是 obscurity，不是授权。

#### Interview Keywords

`vertical guarded + tested per cell` `identity never from body` `scope predicate inside the query` `IDOR shape acknowledged`

---

## Q17-05 如何防止数据泄露？

#### Short Answer

AI 平台的泄露面和普通系统不同：数据可以经**模型输出**出去、经**prompt 出域**到第三方 API、经**日志/审计**沉淀、经**缓存与向量索引**越权、经**引用标题**旁路。我对前三种各有一道控制，后两种是缺口。

#### Standard Answer

`[MY DESIGN]` 按泄露路径列表（这张表是我面试想写的东西）：
| 泄露路径 | 我现在有 | 缺口 / `[PRODUCTION_NEXT]` |
|---|---|---|
| 模型输出带出内容 | 引用与来源强制 + 「资料不足必须拒答」策略 + 答案只来自检索片段 | 无输出侧敏感实体过滤（人名/密钥格式/身份证号正则）；无「密级 → 允许输出粒度」策略（有的文档只能给标题不能给全文） |
| prompt 出域到第三方 API | 默认 `LLM_PROVIDER=mock`（**默认不外发**）、provider 需显式配置 | 无「出域白名单字段 + 脱敏前置」；`[INFERENCE]` 恒光是上市公司，工艺/经营数据出域需要制度化决策 |
| 日志沉淀 | 结构化字段白名单（`FIELD_KEYS`）+ `LOG_JSON` 单行 | 无日志留存期与访问控制策略；工具错误信息带异常类型名与截断 message（可控但需盯） |
| 审计沉淀 | 集中净化：denylist + 长度 + 截断 + key 上限，且**不记 prompt 正文** | 审计表可写（非 append-only）、`audit:read` 无属主范围 |
| 缓存 / 向量索引 | 没有缓存（所以这条通道不存在） | 一旦加缓存：`[MY DESIGN]` key 必须含 principal + 权限集，否则缓存本身就是越权通道（这是我在 Q9-06 里写进集成清单的一条） |
| 引用旁路 | 引用只在有权限的检索结果里产生 | 标题/摘要本身可能敏感 → 需按 ACL 渲染 |
| 仓库/镜像 | `.gitignore` 排除 `.env`、`data/runtime/*`；文档与合成数据目录容器内 `:ro` | 无 secret 扫描（gitleaks）；无镜像 CVE 扫描 |
**我认为最重要的一条判断**：这个 Demo 里数据泄露面小，**不是我设计得多安全，而是数据全是公开资料 + 合成数据**（`[FACT]` README 声明与 `data/synthetic/README.md` 都写明了）。我绝不把「没有发生泄露」当「防护有效」。真实企业内部平台的泄露防护重心在**数据分级 + 出域策略 + 检索层 ACL**，这三件我都还没做，只是把它们写在了改进清单里。

#### My Project Evidence

- `app/observability/audit.py`（净化）、`app/observability/logging.py`（字段白名单）
- `app/rag/prompt.py`（回答策略含「不得虚构数字/财务」与「只使用公开资料」）
- `app/gateway/router.py`（默认 mock ⇒ 默认零外发）
- `.gitignore`、`docker-compose.yml`（`:ro`）、`data/synthetic/README.md`（合成声明）

#### Follow-up Questions

- 如果只能做一件事防泄露，你做哪件？（检索层 ACL——因为它同时管住了答案、引用、缓存和日志四个下游；这也解释我为什么把 Q7-14 当作第一优先缺口）
- 数据分级谁定？（业务/密级 owner 定级，平台只执行；平台自己「猜密级」是最坏设计）
- DLP 要不要？（内部平台我会先要「出域清单 + 审计 + 审批」，DLP 是第三步；`[需要本人确认：公司是否已有 DLP 与出域制度]`）

#### Pitfalls

- 不要说「我们有完整的数据安全体系」。
- 不要把「没有缓存」说成深思熟虑的安全设计，它是「本期没做」——但**「加缓存时 key 必须含权限」这条判断**可以讲，说明我想到过。

#### Interview Keywords

`five leak paths` `default no egress` `ACL gates four downstreams` `cache key includes principal`
# 18 · Docker 与部署

## Q18-01 怎么用 Docker 部署这个平台？

#### Short Answer

`docker compose up --build` 起两个容器：API（`python:3.11-slim` + uv，`:8000`）与 Web（`node:22-alpine` 构建 → `nginx:1.27-alpine`，`:3000`）。数据在 `./data/runtime` 卷里，`depends_on: service_healthy` 保证不 502。

#### Standard Answer

`[MY DESIGN]` `docker-compose.yml` 的关键决定（每条都有理由，不是抄模板）：
① **两个服务，一个 compose 文件**，没有引入 registry/orchestrator——`[FACT]` SPEC 本期明确禁止 K8s；
② **数据分区挂载**：`./data/runtime`（可写：SQLite + Chroma）、`./data/documents:ro`、`./data/synthetic:ro`。**只读挂载是刻意的**：运行期容器不该能改自己的语料与种子数据；
③ **`env_file: path: .env, required: false`**——干净 clone 不需要 `.env` 也能起（默认全 mock），这是 `[FACT]` SPEC「零 Key 可运行」要求在部署层的体现；
④ **healthcheck 用 python 而不是 curl**：slim 镜像里没有 curl。我为了不装一个包而用 `python -c "import urllib.request;urllib.request.urlopen(...)"`，注释写在 compose 里；
⑤ **`depends_on: {api: {condition: service_healthy}}`**：否则 nginx 起在 API 之前，第一次进 Dashboard 会看到 502。
`[MY DESIGN]` 一个我特意处理的 nginx 细节：`proxy_pass` 用**变量 + Docker 内嵌 resolver**（`resolver 127.0.0.11 valid=10s`），这样 `api` 是**每请求解析**而不是启动时解析。直接写 `proxy_pass http://api:8000` 的常见后果是 API 重启/尚未起来时 nginx 崩在 `host not found in upstream`。这是我在 WSL 里真被咬过之后改的。
**镜像层**：`api.Dockerfile` 把依赖安装放在 COPY 代码之前（`uv sync --frozen --no-dev --no-install-project`），所以改代码不重装依赖；`--no-dev` 保证镜像里没有 pytest/ruff；`PYTHONDONTWRITEBYTECODE=1` + `PYTHONUNBUFFERED=1`（容器里日志要即时可见）。
**验证过的路径**：`up --build` → `/health` 200 → 浏览器 3000 跑通六步演示 → `stop` 再 `up -d` 后**审计行数、Chroma 文档数、旧 request_id 的轨迹都还在** → `down -v` 后重启回到干净状态。

#### My Project Evidence

- `docker-compose.yml`（两个服务 + 三种挂载 + healthcheck 注释）
- `docker/api.Dockerfile`（uv 分层、`--no-dev`、`EXPOSE 8000`）
- `web/Dockerfile`（多阶段：node 构建 → nginx 运行）
- `web/nginx.conf`（resolver + 变量 upstream + `try_files $uri /index.html`）
- `README.md` §Docker 部署、§已知限制（明确写了「单节点 compose，不是 K8s」）

#### Follow-up Questions

- 生产上和这个 Demo 有什么不同？（镜像进 registry + tag 策略（语义版本 + git sha）、CI 构建而非本地 build、secrets 从 Vault 注入、TLS 终止、反代与内网边界、备份与恢复演练、日志与指标外送）
- 为什么要挂 `:ro`？（不可变语料 + 降低被攻破后的写入面；语料变更走受控发布流程重新 ingest，而不是热改文件）
- 两个容器怎么扩缩？（api 可多副本，但 SQLite/Chroma 是本地文件卷 → 多副本会各写各的。**所以横向扩展的前置条件是先换 Postgres + 独立向量服务**，这是我认为最诚实的扩展性回答）

#### Pitfalls

- 不要说「Docker 化就完成了生产部署」。我只到「单机可复现运行 + 数据持久 + 健康检查」，没有 registry/CI/编排/备份。
- 不要说 compose 里跑通了 K8s 的东西；`[FACT]` 我没上过 K8s，SPEC 也禁止（§5 有专门答案）。

#### Interview Keywords

`two services one compose` `:ro corpus mounts` `healthcheck-gated depends_on` `resolver + variable upstream`

---

## Q18-02 为什么 nginx 反代而不是 CORS？

#### Short Answer

同源就不需要 CORS：静态资源、`/api`、`/health`、`/metrics` 全从 `:3000` 走，nginx 转给 `api:8000`。少一类配置、少一类预检失败、少一处「生产与开发行为不同」。

#### Standard Answer

`[MY DESIGN]` 三处配合：
- 容器：`web/nginx.conf` 声明 `/api/`、`= /health`、`= /metrics` 三个 location 全部代理到上游；`location / { try_files $uri /index.html; }` 支撑 SPA 前端路由（刷新 `/audit` 不 404）；
- 开发：`web/vite.config.ts` 的 `server.proxy` 把同样三个前缀代理到 `127.0.0.1:8000` —— **dev 与 prod 走同一套相对路径**，前端代码里没有任何 host 判断；
- 后端：`app/main.py` 没有 `CORSMiddleware`（**我根本没装这一层**），API 的 origin 认知是「由反代保证同源」。
额外收益：nginx 是唯一的对外入口（`:3000`），API 的 `:8000` 只在 compose 内部网络里被访问（虽然我也映射了 8000 便于 curl 演示，我会在面试里指出「生产应该去掉这个映射」）。
**代价我也说**：`proxy_read_timeout 120s` 意味着长 Agent 请求由 nginx 决定断不断；`client_max_body_size` 我没设（默认 1m），大文件上传场景要显式配——这是我发现的一个待补项（生产上要按文档大小定）。

#### My Project Evidence

- `web/nginx.conf`（三个 location + resolver 注释）
- `web/vite.config.ts`（同样的三个前缀 + 注释「the API never needs CORS」）
- `app/main.py`（无 CORS 中间件 = 可 grep 证明）
- `README.md` §快速开始（dev 模式端口说明）

#### Follow-up Questions

- 前端怎么带 Authorization？（我的 console 是 localStorage 里的 demo token + 每请求注入 header，**没有 cookie**，所以也不涉及 CSRF cookie 问题；`[PRODUCTION_NEXT]` 真 SSO 会话我会用 httpOnly cookie + SameSite + CSRF token，那时候同源就更有价值了）
- 什么情况下你反而要用 CORS？（前后端不同域且无法放同一入口（比如静态站托管在 CDN）；那时也要白名单 origin 而不是 `*` + credentials）
- 网关层还该做什么？（真实 client IP 透传（现在 `X-Real-IP` 已设，但 `proxy_set_header X-Forwarded-*` 不全）、请求体大小上限、限流、访问日志格式与 request_id 头透传）

#### Pitfalls

- 不要说「同源所以安全」。同源只解决跨源机制问题，鉴权仍然每请求由后端判。
- 不要说「生产部署我做好了」。我只是把本地/演示拓扑做对了。

#### Interview Keywords

`same-origin by design` `dev/prod identical paths` `SPA try_files` `proxy_read_timeout budget`

---

## Q18-03 健康检查怎么做？

#### Short Answer

`GET /health` 报 status/version/请求数 + 数据库探针（4 张业务表的行数与 seeded 布尔），公开无需 token；compose 用它做 healthcheck 与 `depends_on` 的门。

#### Standard Answer

`[MY DESIGN]` 我的取舍：这是**liveness + 一点 readiness**，不是全链路深度检查。它检查「进程活着 + 数据库初始化了 + 业务表有数据」，**不** ping provider、**不** ping Chroma。为什么不 ping 外部模型：如果 provider 挂了 `/health` 变红，编排器会重启一个没有任何问题的进程，并把「外部依赖故障」伪装成「我们的服务坏了」——这在我的错误设计里已经有 502 表达，不该由 health 抢戏。
`database.seeded = bool(rows) and all(rows.values())` 这一条是刻意的：平台可以在表结构存在但数据没播种的状态下启动（那时 ERP 工具会返回 DB 错误），health 应该能看出来。
三个我准备讲的诚实点：① 它公开无鉴权，暴露的是「哪些表有多少行」这种运营信息，我判断演示环境可接受、生产要么加 token 要么拆成 `/healthz`（对外）与 `/readyz`（内网）；② 它**不检查 Chroma**，而知识库为空的真实故障模式（`_require_content` 会 409）不会在 health 上体现；③ 没有 `startup` 探针的等价物，靠 compose 的 `start_period: 40s` 兜住冷启动（Chroma 首次加载慢）。
`[PRODUCTION_NEXT]` 生产上我要的四层：进程存活（liveness）/ 依赖就绪（DB、向量索引、provider 目录）/ 关键指标可达（能否写审计）/ 版本与配置指纹（当前 provider 与模型、知识库快照版本）——最后一项在「为什么这台实例的行为不一样」的排障里最值钱。

#### My Project Evidence

- `app/api/health.py`（`business_tables` 四张表、`tables: len(Base.metadata.tables)`、`request_count`）
- `docker-compose.yml`（healthcheck 用 python urllib，`interval 15s / timeout 10s / retries 5 / start_period 40s`）
- `web/nginx.conf`（`= /health` 反代，前端 Dashboard 直接读）
- `tests/integration/test_platform.py`（health 端点与字段）

#### Follow-up Questions

- provider 挂了要不要让 health 变红？（不要，理由如上；但要让**指标与告警**变红）
- 你要不要 readiness 和 liveness 分开？（要，`[PRODUCTION_NEXT]`；现在只有一个，我会指出这是简化）
- 谁来清理 `data/runtime`？（运维；我给出的是「删卷即重置」，`docker compose down -v` 可验证，这也是我演示数据治理的一个说法）

#### Pitfalls

- 不要说「我们的 healthcheck 覆盖了所有依赖」。它故意不覆盖 provider 和 Chroma，说错了会被要求解释为什么（而正确答案是「不想让外部故障触发重启风暴」，得先想清楚才能讲）。

#### Interview Keywords

`liveness with DB probe` `no provider ping on purpose` `start_period for cold Chroma` `readyz vs healthz next`

---

# 19 · Python / FastAPI 工程

## Q19-01 为什么用 FastAPI？

#### Short Answer

因为我要的三样东西它原生给：Pydantic v2 的入参/出参契约、依赖注入（我的鉴权与 request_id 全靠它）、async 路由。而且它是单进程可部署的最小选择。

#### Standard Answer

`[MY DESIGN]` 具体对应到我这个项目：
- **契约**：每个端点都有 `response_model`（`ChatResponse`、`SearchResponse`、`AgentRunResponse`…），入参 `min_length/max_length/ge/le/pattern` 都在 Pydantic 层，所以我不用在路由里手写校验；422 由统一 handler 转成信封；
- **依赖注入**：`require(Permission.X)` 是**依赖工厂**，路由声明式拿到已鉴权的 `CurrentUser`；`Annotated` 别名（`RequestIdDep`、`AuditLogDep`、`KnowledgeServiceDep`）让签名可读；测试能 override `get_current_user`（`conftest` 就干了这事），这是**可测性**而不只是方便；
- **异步**：provider、DB、向量检索都在 async 路径上；我的中间件是纯 ASGI（不是 `BaseHTTPMiddleware`）——这个选择有具体理由：纯 ASGI **不缓冲响应**，为将来流式输出（SSE）留了路，而且避开 `BaseHTTPMiddleware` 已知的上下文与流式行为坑；
- **异常层次**：`PlatformError` 子类 + `exception_handler`，错误语义不需要在路由里 return；
- **文档**：`/docs` 自动 OpenAPI，演示时能当场看契约（也是 `[FACT]` README 列出的验证项之一）。
**它没给我的、我自己补的**：配置（`Settings` 是普通 frozen dataclass + env 读取，没用 pydantic-settings）、审计、指标、结构化日志、错误信封（`_CODE_BY_STATUS`）、统一 request_id。
**为什么不 Flask/Django**：Flask 我要自己攒契约与 DI（或引第三方），Django 会带来我不需要的 ORM/admin/auth 栈（`[MY DESIGN]` 我用 SQLite 只做只读业务查询 + 一张审计表，Django 的整个模型层是浪费）。

#### My Project Evidence

- `app/main.py`（lifespan 装配、`add_middleware`、`register_exception_handlers`、`include_router`）
- `app/api/router.py`（模块注释解释了为什么路由装配要单独一个文件：避免 `app/api/__init__.py` 造成 agent ↔ api 的**循环导入**）
- `app/auth/dependencies.py`（依赖工厂 + `Annotated`）
- `app/observability/middleware.py`（纯 ASGI + 注释「no response buffering, safe for future streaming」）
- `pyproject.toml`（fastapi/uvicorn/pydantic/httpx/sqlalchemy/chromadb/pyyaml/pypdf，共 8 个运行依赖）

#### Follow-up Questions

- FastAPI 的依赖注入和 DI 容器比差在哪？（我的服务是进程级单例（`get_agent_service` / `get_knowledge_service`），依赖图简单，不需要容器；测试用 `app.dependency_overrides` 就够）
- 流式输出怎么做？（纯 ASGI 中间件已不缓冲；路由换 `StreamingResponse` + 网关加 `chat_stream`，provider 侧 httpx `stream=True`。**我没做**，但路径清楚）
- 为什么 `Settings` 不用 pydantic-settings？（Day 1 时它不在依赖里，我用了 dataclass + 三个小 helper；`[MY DESIGN]` 现在换过去成本很低且能白拿类型校验与错误报告——我会诚实地说这是「够用但次优」的选择）

#### Pitfalls

- 不要说「FastAPI 自动做了鉴权/校验/审计」。它只给了挂载点。
- 不要为了显得深而说「我避开了 BaseHTTPMiddleware 的内存泄漏」——我的准确理由是**不缓冲响应 + 上下文传播**，说不上来的名词别用。

#### Interview Keywords

`response_model contract` `require() dependency factory` `pure ASGI middleware` `8 runtime deps`

---

## Q19-02 async / await 注意点？并发请求怎么处理？

#### Short Answer

三条纪律：不要在 async 路径里做阻塞 IO；共享状态要么不可变要么加锁；依赖图保持 async 贯通。并发上 uvicorn 单事件循环 + 线程安全的进程内状态，但 SQLite 与 Chroma 的并发特性我按「低并发内部平台」假设处理。

#### Standard Answer

`[MY DESIGN]` 我在这个项目里真实处理过的点：
① **没有阻塞调用混进 async**：provider 用 `httpx.AsyncClient`（不是 requests）；DB 是 SQLAlchemy 同步引擎，我**没有**把它包进 `async def` 里跑线程池的复杂机制——这是我知道的一个理论缺陷（同步 DB 调用会阻塞事件循环），在演示并发下没暴露，`[PRODUCTION_NEXT]` 要么 async engine（`aiosqlite`/`asyncpg`）要么 `run_in_threadpool`，我会主动说这一条；
② **共享状态的并发安全**：`Metrics` 用 `threading.Lock`（因为它被中间件与工具层在不同上下文调用）；`Database` 用锁保护 engine 懒创建；`AuditLog` 的 deque 是 CPython 下的原子 append（我在测试里不依赖跨线程顺序，所以够用，生产我会用显式锁或队列）；
③ **单例与 late-bound 配置**：`gateway` / `metrics` 是模块级单例，但配置每次从 `get_settings()` 读——这样测试可以 `update_settings(...)` 改变行为而不必重建对象（`test_gateway.py` 的 fallback 用例就是这么测的）；
④ **contextvar 而不是参数透传 request_id**：日志与错误信封都能拿到 id，而不需要给每个函数签名加一个 `request_id` 参数。这是**上下文传播**，不是隐式依赖——身份（Actor）我仍然是显式传的。
**为什么身份要显式传、request_id 却可以 contextvar**：身份的**错误传播会造成安全问题**（串号 = 越权），所以它必须出现在参数表里、可被类型检查、可被测试固定；request_id 只影响可观测性，错了不越权。这条区分是我在写的时候真正想过的，面试里我愿意讲这个。
`[MY DESIGN]` 并发模型现状：uvicorn 单 worker 单事件循环（`api.Dockerfile` 的 CMD），所以**没有多进程共享状态问题**，也**没有并行度**。「一个慢 provider 请求会占住这个 worker 的什么？」——它不占 CPU，但它占连接与（同步 DB 调用时的）事件循环。这也是我说生产要先换 async engine 的原因。

#### My Project Evidence

- `app/gateway/openai_compatible.py`（httpx 异步）
- `app/observability/metrics.py`（`threading.Lock`）
- `app/observability/logging.py` + `middleware.py`（ContextVar / contextmanager 作用域）
- `app/agent/runtime.py`（`await` 链贯通 gateway 与 executor）
- `tests/conftest.py`（`asyncio_mode = "auto"`）+ `pyproject.toml`
- 已知理论缺陷：`app/db/database.py`（同步 `create_engine` + `session()` 上下文管理器）

#### Follow-up Questions

- 怎么给 Agent 加并行工具调用？（无依赖的 tool_calls 用 `gather`，但要处理**部分失败**与**预算原子扣减**（`state.tool_results` 现在靠顺序 append，并行后要加锁或改累加器），以及审计行的顺序语义）
- 事件循环被阻塞怎么发现？（`asyncio` 的 slow callback 日志 / py-spy / 压测看 P95 与 CPU 的背离；我没有做，但知道该做）
- 为什么不用多 worker 提高吞吐？（多 worker 会让进程内 `Metrics` 与 `AuditLog` 内存缓冲各算各的，`/metrics` 就不准了——**我选单 worker 是有意的语义决定**，不是不知道 `--workers`）

#### Pitfalls

- 不要说「我全异步」。同步 SQLAlchemy 在 async 路由里跑，这是我明确承认的一处。
- 不要说「asyncio 天然线程安全」。
- 不要把 contextvar 说成万能：身份绝不走 contextvar。

#### Interview Keywords

`no blocking IO in async paths (mostly)` `lock shared mutable counters` `identity explicit, correlation contextual` `single worker is a semantic choice`

---

## Q19-03 Pydantic 用在哪？

#### Short Answer

四个地方：API 入参（带边界与 pattern）、API 出参（`response_model`）、**工具参数 schema（并作为 OpenAI function schema 的单一来源）**、配置与错误负载。校验只写一次，模型侧与人侧都受益。

#### Standard Answer

`[MY DESIGN]` 最有含金量的是第三点：`app/agent/tools/base.py` 的 `Tool` 有一个 `args_model: type[BaseModel]`，`validate()` 做执行前校验并返回 `model_dump()`，`to_openai_schema()` 直接用 `model_json_schema()` 生成 `parameters`。**所以「模型被告知的形状」和「我被校验的形状」是同一个定义**，不会漂移。`tests/unit/test_permissions.py::test_schemas_are_generated_for_every_tool` 钉住这条。
边界我怎么写：`days: int = Field(default=30, ge=1, le=365)`、`limit: ge=1 le=50`、`operation: Literal[七个值]`、`message: str = Field(min_length=1, max_length=8000)` + `field_validator` 把纯空白判掉、`mode: pattern="^(auto|chat|agent)$"`、`MAX_REQUEST_STEPS=20` 与 `MAX_TOP_K=20` 这种**服务端硬上限**（用户可以覆盖，但不能越过我）。
另外两处：错误信封里的 `details`、`app/api/*.py` 的响应模型（前端契约由 `web/src/types/index.ts` 的 TS 类型镜像，并由 30 个契约测试钉住两端一致）。
`[MY DESIGN]` 一个我刻意不做的用法：**不用 Pydantic 当 ORM**（SQLAlchemy 的 `Mapped[]` 声明在 `app/db/models.py`），也不把内部模型直接当响应模型——两者形状不同、演化节奏不同。
**校验失败的用户体验**：路由层是 422 + `details.errors`（过 `_json_safe`）；工具层是 `INVALID_ARGUMENTS` + **字段级摘要回灌给模型**（`_validation_summary`），因为模型是「有机会改正的调用方」，人不是。这个区别我认为是 AI 平台设计里一个真实的新问题。

#### My Project Evidence

- `app/agent/tools/base.py`（`args_model` / `validate` / `to_openai_schema`）
- `app/agent/tools/{erp,safety}.py`（Literal + ge/le/max_length）
- `app/api/{chat,knowledge,agents}.py`（入参边界 + `response_model`）
- `tests/unit/test_erp_tool.py`（26）、`test_safety_tool.py`（17）、`test_agent_tools.py`（17）
- `web/src/types/index.ts`（前端镜像类型，272 行）

#### Follow-up Questions

- schema 太多导致模型选错怎么办？（工具数量比 schema 复杂度更影响选择准确率 → 按角色/意图裁剪，见 Q8-11）
- `model_json_schema()` 生成的 schema 有什么不友好的地方？（Pydantic 会加 `title` 等噪声字段、`anyOf` 表达 Optional、描述太长会挤占上下文；我会做一层 schema 清洗，`[PRODUCTION_NEXT]`）
- 校验规则该写模型里还是 executor 里？（**两层都要，理由不同**：模型里是「形状合法」，executor 里是「这组参数被授权」——比如 `operation` 在 Literal 与 `operations` 字典里各查一次，前者防幻觉、后者防「新加了 operation 却忘了配权限」）

#### Pitfalls

- 不要说「Pydantic 保证了安全」：它保证形状，不保证授权与语义正确。
- 不要说「出参也有 schema 强制校验」——我用 `response_model`，但工具 payload 的内部结构是约定而非模型（这是 §22 的一条小缺口）。

#### Interview Keywords

`single source for model-facing and server-side schema` `server-side hard caps` `field-level feedback to the model` `validation ≠ authorization`

---

## Q19-04 项目里用了哪些设计模式？

#### Short Answer

四个真在代码里的：Protocol/接口抽象（provider、embedding）、工厂 + 依赖注入、注册表 + 执行器（白名单边界）、适配器（`BusinessQueryTool` 把 DB 查询适配成 Tool）。外加一个中间件与一个单例。我不给它们套「23 种模式」的名号。

#### Standard Answer

| 模式 | 在代码里的位置 | 它实际解决的问题 |
|---|---|---|
| **Protocol（结构化子类型）** | `app/gateway/base.py::ModelProvider`、`app/embeddings/base.py` | 不要求继承就能被测试注入 fake；`isinstance` 检查靠 `@runtime_checkable`（有测试） |
| **工厂 / 装配** | `build_embedding_provider()`、`build_default_registry()`、`get_*_service()` | 「读配置决定用哪个实现」集中一处；测试可注入 |
| **注册表 + 执行器** | `ToolRegistry` / `ToolExecutor` | 能力面与授权点分离：registry 决定「存在」，executor 决定「允许」 |
| **模板方法 + 适配器** | `BaseProvider.chat`（参数校验在基类）、`BusinessQueryTool`（子类只给 operations 映射） | ERP 与 Safety 两个工具共享 80% 逻辑（渲染、payload、错误、审计），差异只在 operation → query 映射 |
| **纯 ASGI 中间件** | `RequestContextMiddleware` | 横切关注（id/延迟/计数）不进业务代码 |
| **单例 + 可替换** | `gateway`、`metrics`、`get_audit_log()/set_audit_log()` | 进程级共享状态；同时给测试留了替换口 |
| **值对象** | frozen dataclass：`ModelResponse`、`CurrentUser`、`Actor`、`AuditEvent`、`ToolResult` | 跨层传递不可变；`Actor.from_user()` 是唯一身份构造点 |
**我刻意没做的模式**（这半段更重要）：没有 Repository/UnitOfWork 抽象层（SQLAlchemy 之上只有 `app/db/queries.py` 的函数，加一层只会多概念）；没有事件总线；没有策略配置化（fallback 是布尔，不是策略对象——`[PRODUCTION_NEXT]`）；没有 DTO 映射层。
`[MY DESIGN]` 我选模式的标准是**「它删掉了一处重复或是重复」**。`BusinessQueryTool` 是全套里唯一真正的收益：ERP 与 Safety 各自从约 200 行缩成一个 operations 字典，而它们的错误语义、审计语义、双视图渲染**不可能被写歪两次**。这条标准我能当场指出代码。

#### My Project Evidence

上表每格都有对应文件；额外证据：`git show 60f7227..bb295b4`（Day 4/5 的重构轨迹里 `business.py` 抽出）；`tests/unit/test_agent_tools.py` / `test_erp_tool.py` / `test_safety_tool.py` 三个文件共享 fake 与断言形状。

#### Follow-up Questions

- 有没有过度抽象的地方？（有，我会指两处：① `chat_service.py` 只剩一行文档字符串的死模块；② `ChatResponse.sources/tool_calls` 是永远不会被 chat 路径填充的字段——我为它写了注释而不是删掉，这是次优选择，见 §21 Fix #9 / §22）
- 什么时候你会把它拆成服务？（当一个边界需要独立扩缩或独立团队时。目前只有向量检索和模型推理有这种潜力，所以我在 §26 的设计里只拆这两块）

#### Pitfalls

- 不要报一串模式名而无代码可指。
- 不要把「没做抽象」说成「不懂抽象」——我给的判据是「删重复才算」，这是更成熟的版本。

#### Interview Keywords

`Protocol for testability` `registry vs executor separation` `template method that deleted real duplication` `no repository layer on purpose`
# 20 · 数据库与 SQL

## Q20-01 数据库怎么设计的？

#### Short Answer

9 张表一个 SQLite 文件：3 张平台表（`users` + `audit_logs` + 隐式）、6 张业务表（供应商/物料/采购订单/库存/安全事件/设备/维修记录）。**参考 DDL 是手写的 `schema.sql`，运行时 DDL 的唯一真相是 ORM**，两者由测试锁一致。

#### Standard Answer

`[MY DESIGN]` 表清单（`app/db/models.py`，`__tablename__` 可 grep）：
| 表 | 角色 | 关键点 |
|---|---|---|
| `users` | 平台 | `role` 带 `CHECK(role IN ('admin','manager','operator'))`，`username`/`token` 唯一 |
| `audit_logs` | 平台 | `user_id` **NOT NULL** + FK；`request_id/action/endpoint/tool_name/model_name/mode/input_summary/status/latency_ms/created_at`；两个索引（`created_at`、`tool_name`） |
| `suppliers` | 业务 | 8 家（`data/synthetic/seed.json`），`category/region/status` |
| `materials` | 业务 | 10 种（原盐、盐酸、液碱、硫酸…硫氯产品链口径），`unit/category` |
| `purchase_orders` | 业务 | ~328 单，FK 到 supplier/material，`quantity/unit_price/order_date/status`，两个索引（`order_date`、`material_id`） |
| `inventory` | 业务 | 9 条快照，带安全库存，所以「低于安全库存」这类查询不需要窗口函数 |
| `safety_incidents` | 业务 | 按 `safety` 段的生成规则造，含 `area/severity/category/created_at` |
| `equipment` / `maintenance_records` | 业务 | 各 6 条，**建了但没暴露工具**（我认为这是最诚实的一处「预留」，见 Q20-06） |
两条我认为值得讲的设计判断：
① **`audit_logs.user_id NOT NULL`**（`[FACT]` SPEC §5.2 定的）带来一个真实行为：401 这种「不知道是谁」的事件**无法**落这张表。我的处理是**不破坏契约**——`AuditLog.record()` 里 `user_id is None` 就只进内存 + `logger.debug`，并在代码注释里写明这个取舍。`[PRODUCTION_NEXT]` 正确做法是拆一张 `unauthenticated_events`（或让列可空 + 显式默认），而不是悄悄丢事件。
② **`created_at` 是 TEXT（ISO 字符串）**，不是 TIMESTAMP。这是 SQLite 场景的务实选择（可读、无需时区驱动行为差异），排序与 `substr(created_at,1,10)` 这类周聚合都能直接用；`[PRODUCTION_NEXT]` 换 Postgres 时要改 `timestamptz` 并统一 UTC + 应用侧带时区。

#### My Project Evidence

- `data/synthetic/schema.sql`（9 表 + 索引 + CHECK/FK）
- `app/db/models.py`（`Base.metadata` 是运行时 DDL 来源）
- `tests/unit/test_database.py`（36 个测试）：表列级一致、种子幂等、FK/CHECK 生效、审计读写、行计数
- `app/db/seed.py`（`load_seed` / `validate_seed` / `ensure_seeded` / `reseed`）

#### Follow-up Questions

- 为什么 `audit_logs` 与业务表同库？（Demo 便利；生产上审计应该**异库异账号**，否则「能改业务的人就能改审计」）
- 数据量怎么估？（审计是唯一会线性增长的表：一次 agent.run ≈ 2–4 行。`[INFERENCE]` 100 名内部用户 × 20 次问答/天 ≈ 6k 行/天 ≈ 200 万行/年 → SQLite 单文件到这个量级已经开始难受，这也是我说审计该独立表/独立库的原因之一）
- 为什么不建外键到 `documents`？（知识正文在 Chroma + 文件系统，不同存储域；`document_id` 是逻辑引用，不做强 FK——这是刻意的边界）

#### Pitfalls

- 不要说「我设计了完整的企业数据模型」。这是 6 张演示表，粒度到「能回答 12 个固定 operation」。
- 不要漏了 `equipment`/`maintenance_records` 存在但无工具这件事——被问到设备场景时说错就更糟（见 Q12-04）。

#### Interview Keywords

`ORM and reference DDL kept in sync by test` `NOT NULL user_id forces an explicit choice` `audit is the only growing table`

---

## Q20-02 SQLite 够用吗？瓶颈在哪？

#### Short Answer

够这个 Demo 用，因为它同时承担「业务只读数据集 + 审计表」两个角色且并发很低。瓶颈是写并发与共享文件系统，不是查询性能。生产上我会迁 Postgres。

#### Standard Answer

`[MY DESIGN]` 我选它的三条理由 + 我做的三件防护：
**理由**：① 零服务、零配置，`docker compose up` 就能持久（`[FACT]` SPEC 本期禁止外部依赖服务）；② 它是「审计 + 小规模业务参考数据」的合理承载；③ 测试可以指向 `tmp_path` 下的临时文件，**测试与生产跑同一套 SQL**（不是 mock 出来的假行为）。
**我做的防护（这半部分才是重点）**：
- 相对路径**永远相对仓库根**解析（`resolve_sqlite_path` / `normalize_url`），否则 `uvicorn` 从不同 CWD 启动会悄悄打开不同数据库文件——这是我真踩过的坑；
- engine 懒创建 + `threading.Lock`（导入应用不碰磁盘）；
- `session()` 是显式上下文管理器（不泄漏连接），并挂了 `event` 钩子；
- **种子幂等**：`ensure_seeded` 重复执行不翻倍（两条测试钉住）。
**瓶颈与迁移触发条件**：SQLite 的写是**整库串行**，多进程共享文件不安全。所以只要出现以下任一条，我就迁 Postgres：多副本应用、审计写入 QPS 上量、需要行级锁/并发迁移、需要真正的备份/复制/PITR。迁移动作在我这儿是**有形状的**：`[MY DESIGN]` SQL 全部集中在 `app/db/queries.py` 的模块级常量里，所以换方言时我改的是「一批常量 + 一个 engine URL」，而不是散在各处的字符串——`julianday(...)` 那类 SQLite 专属函数是我最需要先替换的（Postgres 用 `date_trunc('week', ...)`）。
`[PRODUCTION_NEXT]` 顺带：向量库与关系库的一致性（文档删了索引没删）在任何数据库选型下都存在，这是**对账任务**的活，不是事务的活（见 Q7-13）。

#### My Project Evidence

- `app/db/database.py`（`resolve_sqlite_path`、`normalize_url`、懒 engine + 锁、`session()`、`table_row_count`）
- `app/config.py::database_url` 默认 `sqlite:///./data/runtime/app.db`
- `docker-compose.yml`（`./data/runtime` 挂卷 = 数据持久化机制）
- `app/db/queries.py`（SQLite 函数只出现在这一处文件）
- `README.md` §已知限制（我自己写了 SQLite 单文件不是生产高并发方案）

#### Follow-up Questions

- pgvector 呢？（`[MY DESIGN]` 如果关系库已经是 Postgres，我会认真评估 pgvector 来消掉一个组件；但我不会为了「少一个组件」先上 Postgres 再上 pgvector —— 顺序要反过来说服自己）
- 你要怎么做备份？（SQLite：`sqlite3 .backup` 或文件级快照 + Chroma 目录一起备，恢复演练要真跑；`[FACT]` 我没做过 PITR；生产我会把审计与业务分开备）
- 审计能不能进 JSON 文件而不进 DB？（可以，但过滤/分页/关联查询就退化成 grep，而 `GET /api/audit?tool=x` 这种是审计的**核心用途**）

#### Pitfalls

- 不要说「SQLite 生产不可用」——很多小型内部系统用它很好；也不要说「我验证过高并发」（没有）。
- 不要说「换 Postgres 只是改 URL」。方言函数、类型系统、并发语义、迁移工具都要动，我能点名 `julianday` 这一处。

#### Interview Keywords

`zero-service constraint respected` `path resolution is the real gotcha` `same SQL in tests and prod` `dialect localized in one module`

---

## Q20-03 如何防止 SQL 注入？

#### Short Answer

三条：SQL 文本永远是模块级常量、值只能走命名参数绑定、模型侧连 SQL 都接触不到（它只选 operation + 有界参数）。前两条防注入，第三条防的是比注入更常见的那一类问题。

#### Standard Answer

`[MY DESIGN]` 逐条给证据（我可以当场 grep）：
```text
_SQL = """SELECT ... FROM purchase_orders po
          JOIN materials m ON m.id = po.material_id
          WHERE po.order_date >= :cutoff
            AND (:material IS NULL OR m.name LIKE :material_like)
          GROUP BY m.id ORDER BY total_spend DESC LIMIT :limit"""
rows = session.execute(text(sql), params).mappings().all()
```
① 没有一处 f-string / `+` 拼进 SQL（`grep` 可证）；② 参数是**绑定变量**，`"%"+material+"%"` 这种 LIKE 模式也是把值绑进 `:material_like`，所以通配符与引号都只是字符；③ `operation` 是 `Literal` 七选一，`days/limit` 有范围，字符串字段有 `max_length`；④ 审计与日志净化把 `content/prompt/token` 之类 key 丢掉，避免把敏感串写进别的地方。
**但我要主动区分两件常被混为一谈的事**：
- **SQL 注入**（让数据库执行我本不该执行的语句）：参数绑定解决；
- **越权读取**（用完全合法的 SQL 读你不该读的数据）：绑定**一点都防不了**，它由权限模型 + 数据范围 + operation 白名单解决。
在 AI 平台上第二类风险远大于第一类，因为**没有任何人写 SQL**。所以真正起决定作用的是「模型能表达什么」这个能力面设计。
`[PRODUCTION_NEXT]` 接真实 ERP 时我会再加四道：只读账号（无 DDL/DML 权限）、独立 schema 或预授权视图、`statement_timeout` + 行数上限、SQL 原文显示给人（ad-hoc 场景下这是审计的一部分）。

#### My Project Evidence

- `app/db/queries.py`（常量 + 绑定参数 + `_run` 里 `SQLAlchemyError` → `BusinessQueryError`）
- `app/agent/tools/erp.py` / `safety.py`（`Literal` + `ge/le` + `max_length`）
- `tests/unit/test_erp_tool.py` / `test_safety_tool.py`（非法 operation / 越界参数被拒的断言）

#### Follow-up Questions

- `LIKE` 拼接安全吗？（值绑定安全；但用户输入的 `%`/`_` 会被当通配符——语义问题不是注入。我会转义或强制前缀匹配，`[MY DESIGN]` 我现在是 `'%' || :material_like || '%'` 形式，通配符扩张是真实存在的，属可控但值得指出）
- ORM 是不是就不用防注入？（不是。`text()` 与 `order_by(字面量)` 都能被拼坏；防注入是习惯不是工具）
- 慢查询会不会被利用成 DoS？（会，这是我最缺的一类防护（无 timeout/无限流），见 Q16-04）

#### Pitfalls

- 不要把 OWASP 名词当答案；要给「这一行代码为什么不可能被拼坏」。
- 不要说「用了 ORM 就防住了注入」。

#### Interview Keywords

`constant SQL + bound params` `injection ≠ privilege escalation` `capability surface is the real defense`

---

## Q20-04 索引怎么加？

#### Short Answer

只加在「被证明会用来过滤/排序」的列上：时间窗、外键连接键、审计的时间与工具维度。没有为了「看起来专业」而加索引。

#### Standard Answer

`[MY DESIGN]` 现有的六个索引（`schema.sql` 与 ORM 一致）：
| 索引 | 服务的查询 | 判据 |
|---|---|---|
| `idx_purchase_orders_order_date` | 所有 operation 都带 `WHERE order_date >= :cutoff` | 表里唯一的时间谓词 |
| `idx_purchase_orders_material_id` | 按物料分组/过滤的 JOIN | 分组键 + 可选过滤 |
| `idx_safety_incidents_created_at` | 安全事件的时间窗与周趋势 | 同上 |
| `idx_audit_logs_created_at` | 审计按时间倒序分页（`ORDER BY a.id DESC` 的近似 + 归档扫描） | 审计是唯一会增长的表 |
| `idx_audit_logs_tool_name` | `GET /api/audit?tool=erp_purchase_analysis` | UI 上真有的过滤器 |
| （`users.username/token` UNIQUE） | token → 用户查找（每次请求） | 唯一约束自带索引 |
**为什么不加更多**：Demo 数据是几百到几千行，SQLite 全表扫与走索引**测不出差别**——在这种数据量上加索引等于用写入成本换一个我不知道的收益。`[PRODUCTION_NEXT]` 我会用**真实做法**：先打开查询计划与慢查询日志（Postgres `EXPLAIN (ANALYZE, BUFFERS)`），按实际执行时间与行数决定；重点会落在「采购订单的 `(supplier_id, order_date)` 复合索引」「审计的 `(created_at DESC, user_id)`」以及高频 operation 的覆盖索引。
我还会说一个容易忽略的点：**复合索引列序**由「等值谓词在前、范围/排序在后」决定，所以 `(:material IS NULL OR m.name LIKE ...)` 这种**可选谓词**会让索引规划变复杂——生产上我更倾向于拆成两个明确的查询路径而不是一个万能 SQL。

#### My Project Evidence

- `data/synthetic/schema.sql`（索引定义）+ `app/db/models.py::__table_args__`（同一批索引）
- `app/db/queries.py`（每个查询的 WHERE/ORDER BY 形状，可与索引对照）
- `tests/unit/test_database.py`（DDL 一致性）

#### Follow-up Questions

- `LIKE '%x%'` 能用索引吗？（普通 B-tree 不能。生产上要么前缀匹配 + `text_pattern_ops`，要么全文索引 / pg_trgm / 交给检索层）
- 你怎么知道某个查询慢？（现在：`/metrics` 端点均值 + 审计 `latency_ms`。没有 per-query 计时是缺口）
- 覆盖索引什么时候值得？（当高频聚合查询能把列全含进索引、避免回表时——但要先有行数与 QPS 支撑）

#### Pitfalls

- 不要背「索引三原则」而不给本地判据。
- 不要说「我做过性能调优」。我做的是「按可预期的访问模式加了 6 个索引」，并知道这在 328 行数据上无收益可测。

#### Interview Keywords

`indexes only where the predicate is` `explain before adding` `optional predicates complicate plans`

---

## Q20-05 事务怎么处理？

#### Short Answer

写入都是**单语句事务**（一次审计 INSERT、或一次种子批量插入），所以我不需要跨语句的隔离级别决策。真正需要原子性的是种子重建，我用「先建临时表再切换/整批插入 + 幂等检查」保证重跑不脏。

#### Standard Answer

`[MY DESIGN]` 现状与判断：
- 审计写入：`with db.session() as s: s.execute(_INSERT_SQL, row)` —— 一个 session 一个 INSERT，提交即完成。**故意不做批量异步落盘**：审计要能立刻被 `GET /api/audit/{request_id}` 查到（Demo 与运维都是这个语义）。
- 种子：`ensure_seeded` 检查是否已有数据，有就跳过；`reseed(force=True)` 整批重建。两条测试钉住幂等（`test_re_running_seed_does_not_duplicate_rows`、`test_force_reseed_rebuilds_the_same_data`）。这是我在本项目里唯一真实处理过「多语句写一致性」的地方。
- **我明确不需要的**：跨表业务事务（这个平台不写业务系统）、分布式事务/saga（没有跨服务写）。
- **我确实缺的**：审计写入失败没有补偿队列（只记 `last_error` + warning），所以「一次故障期间的审计缺口」在今天是**不可见的**。`[PRODUCTION_NEXT]` 我会加：写失败计数指标（现在只有 `audit_write_count` 成功计数，**没有失败计数**——这是我复查时发现的一处真实不对称）+ 本地暂存队列重投 + 「审计缺口」本身作为一条告警。
`[PRODUCTION_NEXT]` 如果将来要写业务系统（第二期），事务边界我的判断是**不在 AI 平台里开跨系统事务**，而是：平台内落一条「待执行 + 幂等键 + 参数快照」的记录 → 由集成流程去写 ERP → 对账回写状态。这是 saga/outbox 的形状，不是两阶段提交。

#### My Project Evidence

- `app/observability/audit.py::record`（单条写 + `except Exception` 兜底 + `_last_error`）
- `app/db/database.py::session`（显式事务上下文）
- `app/db/seed.py`（幂等 + `force` 重建）
- `tests/unit/test_database.py`（36，含两条幂等断言）

#### Follow-up Questions

- 审计写失败你怎么发现？（**目前只有日志**，没有指标与告警——我会补失败计数，并承认这是不对称）
- SQLite 的并发写你怎么处理？（单进程 + 单写者，够用；多进程就会遇到 `database is locked`，这也是我把它列为迁移 Postgres 首要触发条件的原因）
- 需不需要 ORM unit-of-work？（不需要。9 张表里只有 2 张会被写，写路径共 3 处，一层 UoW 只会增加概念）

#### Interview Keywords

`single-statement writes by design` `seed idempotency is my only real transaction` `audit failure counter missing` `outbox not 2PC`

---

## Q20-06 为什么选 SQLite + Chroma 而不是 Postgres + pgvector？

#### Answer

见 **Q5-10 / Q5-11**（选型完整论证）+ **Q20-02 / Q20-07**。
补一句我认为最成熟的表述：这两个选择**都是本期约束下的选择，不是我的技术偏好**。如果明天给我 Postgres 实例和一个可写内部库，我第一件事是换掉 SQLite（为了审计的独立账号与备份），第二件事是**保留** Chroma（因为它让「向量库是被替换的实现」这件事在代码上成立：`app/rag/store.py` 是唯一碰它的模块）。**能便宜替换的抽象，比一开始就选对的具体组件更值钱**——这是我想传达的判断。

---

## Q20-07 数据是怎么造的（合成数据）？

#### Short Answer

手写目录（供应商/物料/设备/用户）+ 声明式生成规则（时间窗、区间、随机种子）+ 固定锚点日期，保证「同一份 seed.json 任何时候重跑都得到同一套数据」，同时让「最近 30 天」这类窗口查询永远有数据。

#### Standard Answer

`[MY DESIGN]` `data/synthetic/seed.json` 的 12 段：`meta / users / suppliers / supplier_preferred_material_ids / materials / purchase_order_options / inventory / safety / purchase_orders / safety_incidents / equipment / maintenance_records`。
关键设计四条：
① **`meta` 里带 `random_seed` 与时间窗/锚点**（`tests/unit/test_database.py` 会断言 `seed.json` 的 `meta.table_counts` 与实际行数一致 —— **数据自证**，这是我认为最有说服力的一处）；
② **时间序列相对「今天」生成**（`ensure_seeded` 的注释写明「Seeded relative to today so that "the last 30 days" always contains rows」）—— 否则演示半年后会查出空表，Agent 就会开始「没有依据地回答」，这是一个非常现实的可复现性陷阱；
③ **物料口径对齐公司公开产品链**（原盐、盐酸、液碱、硫酸、氯酸钠、三氯化磷等），使 Agent 的回答看起来像一个氯碱/硫化工企业的采购结构 —— 但 `data/synthetic/README.md` 明确声明「与恒光股份真实经营数据没有任何关系」；
④ **表间引用用 id**，`supplier_preferred_material_ids` 这类关系表让「供应商集中度」这种 operation 有真实形状。
规模：3 用户 / 8 供应商 / 10 物料 / ~328 采购订单 / 9 库存快照 / 若干安全事件 / 6 设备 / 6 维修记录。
`[需要本人确认：是否需要把 seed 规模调大到能体现分页/limit 差异的程度]`
**一个我要主动承认的错误**：`data/synthetic/README.md` 里把公司代码写成了 **301109.SZ**，而恒光股份的正确的是 **301118.SZ**（301109 是另一家公司，见 §来源）。这处是我复查仓库时发现的**事实性错误**，**已在最终一致性修复提交中改为 301118.SZ**（`README.md` 与 `seed.json` 两处都改了；见 §22 / §21 / §34 #3）。

#### My Project Evidence

- `data/synthetic/{seed.json,schema.sql,README.md}`
- `app/db/seed.py`（`load_seed` / `validate_seed` / `ensure_seeded` / `reseed`）
- `tests/unit/test_database.py`（seed 校验、计数一致、幂等、force 重建）

#### Follow-up Questions

- 为什么不直接用公开年报数据？（年报只有公司级合并数字，撑不起「按区域/物料/时间」的查询；而且把真实财务数据当业务明细会让演示边界变得含糊）
- 造数据最容易错在哪？（**引用完整性与时间语义**：外键指向不存在的 id、事件时间在未来、比率与计数不自洽。我用 schema CHECK + 固定 seed + 计数断言三件来防）

#### Pitfalls

- 不要说「我造了接近真实规模的数据」。328 行订单不是企业规模。
- 不要把合成数据说成「恒光的采购数据」——它是**结构像**，数值是编的。

#### Interview Keywords

`declarative seed with fixed rng` `anchor relative to today` `self-verifying row counts` `structural realism not scale`

---

# 21 · 代码审查发现与修复（Audit Fix）

## Q21-01 你是怎么做代码审查的？

#### Short Answer

把「这个平台哪里会出错」变成一份可判定的检查清单，逐条对着代码找，找到问题就**先写一个能复现的失败测试再修**，最后一次性提交（`460a6ee`）。审查记录有 10 条，其中 9 条在这次提交里落地。

#### Standard Answer

`[MY DESIGN]` 我的检查清单（按这次真正问出结果的问题类型排）：
| # | 检查问题 | 结果 |
|---|---|---|
| 1 | 每条**失败路径**都写了审计吗？ | ❌ `POST /api/chat` 失败时抛 502 但**没有审计行**（只有成功路径写） |
| 2 | 有没有「静默改变行为」的默认值？ | ❌ provider 失败**无条件降级到 mock**，还返回 200，用户与审计都不知道模型换了 |
| 3 | 错误响应会不会泄露凭据/内部结构？ | ❌ 401 的 details 里把三个 demo token 全列出来（虽然是公开凭据，但**这个形状**在生产等于泄露） |
| 4 | 授权检查在所有入口都 fail-closed 吗？ | ❌ `ToolExecutor` 的写法是 `if actor is not None and not has_permission(...)` —— `actor=None` 时**跳过检查直接执行**（今天只有测试会传 None，但这是最坏的一种默认） |
| 5 | 有没有无界增长的内存结构？ | ❌ 审计的内存副本是 `list`，永不释放 |
| 6 | —（记录里有，本次未落地） | — |
| 7 | 有没有死代码/误导性的 API？ | ✅ `users.py` 里有一段无用分支 → 删除 |
| 8 | 状态码到错误码的映射齐全吗？ | ❌ `429` 不在映射表里，会被标成 `INTERNAL_ERROR` |
| 9 | 响应模型有没有永远不会被填充的字段？ | ⚠️ `ChatResponse.sources/tool_calls` 在 chat 路径恒为空 → 我加了文档注释说明，**没有删**（这是我复查后仍不满意的处理，见 Q21-04） |
| 10 | 前端有没有无意义的代码？ | ✅ `AgentPlayground` 里一个恒真的 className 条件 → 清理 |
**这套清单的来源我要诚实说**：它不是「最佳实践背诵」，是我按这个项目的**具体风险面**列的——AI 平台里我最担心的是「静默失败」和「默认放行」这两类，所以第 1/2/4 条是我特意先问的。
**修复方式**（每条都对应一次可指的行为变化 + 测试）：见 Q21-02 / Q21-03。
提交：`git show 460a6ee`（9 项修复 + 测试；`README/ARCHITECTURE/DEMO_SCRIPT/SPEC` 同步更新）。

#### My Project Evidence

- `git log -1 460a6ee`（提交信息逐条列了 Fix #1–#10）
- 变更文件：`app/{api/chat.py,api/errors.py,agent/executor.py,auth/dependencies.py,config.py,gateway/base.py,gateway/router.py,observability/audit.py}`
- 测试新增：`tests/integration/test_chat.py`（+68 行，含失败路径审计与 provider 异常注入）、`test_rbac.py`、`tests/unit/test_agent_permissions.py`
- 测试数从 `380`（Day 4 后）→ Day 5 `410` → 本提交 `420` → **后续 `422 passed` → 当前 `423 passed`**（本轮新增 2 条 `AuditLog.clear()` 回归测试；README 已同步为 422 并把旧数字标为历史轨迹，见 §34）

#### Follow-up Questions

- 为什么不一开始就写对？（#1 和 #4 是我在 Day 4 加平台层时**为了先跑通**留下的形状；我现在的做法是把这份清单前置到编码阶段——这也是我 5 天做完能交付的原因，但它确实有代价。我会承认这个权衡）
- 你一个人审自己，效率会不会很低？（会。所以我把「审什么」写成可判定问题而不是「读一遍代码」。更有效的是换人 + 自动化，我缺 linter 规则、类型检查严格模式、依赖扫描、git-secrets——这些我都列在 §22）
- 审出来的问题怎么排优先级？（**能否被静默地造成错误结论**优先。#2 排在最前，因为它会让平台「看起来在工作」而实际在骗人）

#### Pitfalls

- 不要说「我审查了代码，修了 10 个问题」——要说清**每一个**的判定问题是什么、错在哪、后果是什么。说不出后果的审查就是找格式问题。
- 不要说 #3 是「安全漏洞」。它是**响应形状缺陷**，凭据本身是公开演示 token。混淆这两点会被安全背景面试官当场纠正。
- 不要说「审查后没有残留问题」。我在复查时又发现了这次提交自己引入的问题（Q21-04）。

#### Interview Keywords

`findings as yes/no questions` `silent failure beats loud failure is the bug` `regression test per fix` `audit found the fix's own defect`

---

## Q21-02 哪些是高优先级缺陷？为什么？

#### Short Answer

四个：静默降级（#2）、工具层越权放行（#4）、审计在失败路径缺失（#1）、内存无界增长（#5）。优先级由「错误会不会被看见」决定，不是由代码行数决定。

#### Standard Answer

**#2 静默 provider 降级 —— 我认为最高优**
原代码：provider 失败就无条件 `return await mock_prov.chat(...)`，响应 200、`provider=mock`，但**没有任何标记**。
为什么最严重：在带引用的知识问答里，用户看到的是一个格式正常、有 `[1]` 引用、内容却是 mock 拼出来的答案。**平台的正确性契约被静默替换，而审计与指标都不知情**。
修复（三件事一起做，缺一件都不算修好）：① `LLM_FALLBACK` 配置门，**默认 false**；② 降级路径重新构造 `ModelResponse(degraded=True)` 让契约可见；③ `logging.warning("provider fallback triggered: %s -> mock")` 留下运维痕迹。
测试：`test_fallback_disabled_raises_error` / `test_fallback_enabled_returns_degraded` / `test_fallback_disabled_no_mock_circuit`（第三条专门钉「mock 失败不再降级」）。

**#4 工具层 `actor=None` 放行**
原代码：`if actor is not None and not has_permission(actor.role, tool.permission)` —— 逻辑上「没有身份 = 跳过授权」。
为什么严重：这是**授权层的 fail-open**。今天的调用方都传了 actor，所以没有可利用路径；但下一个人加一条新入口忘了传 actor，**工具就对匿名身份全开放**，而且审计里的身份会变成默认 `Actor()`（anonymous）。
修复：先判 `if actor is None or not actor.is_authenticated: return PERMISSION_DENIED`，再判角色权限。也就是**把「有身份」变成授权检查的前置条件而不是可选条件**。
测试：`tests/unit/test_agent_permissions.py`（+23 行）断言无身份 actor 被拒。

**#1 失败路径不写审计**
原代码：`status = AuditStatus.SUCCESS` 在 try 之前设好，except 分支里直接 `raise ProviderError`，**从没调 `record`**。
为什么严重：模型不可用恰恰是最需要证据的时刻（谁在什么时候试了、失败了、错误类型是什么）。而且它让「可用性指标」与「审计」互相矛盾：`error_by_code.PROVIDER_ERROR` 有计数，审计里却查不到对应记录。
修复：except 分支里先算 latency、写一条 `chat.complete=error`（`{chars, error_type}`，不含 prompt），再抛 502。
测试：`tests/integration/test_chat.py::TestAuditOnFailure::test_failed_chat_writes_audit`（用 `patch.object(gateway, "chat", failing_chat)` 注入真实异常）。

**#5 审计内存无界**
`self._records: list[AuditEvent] = []` 每写一条 append 一次，永不清理 → 长跑进程的内存泄漏。
为什么排第四而不是更高：它只在长时间运行时发生，不会造成错误结论。但它**是我这次审查里唯一一条「不修就一定出问题」的资源类缺陷**，因为它是必然发生而不是概率发生。
修复：`deque(maxlen=settings.audit_memory_max_records)`（默认 1000），可配置。

#### My Project Evidence

`git show 460a6ee` 里每个文件的 diff；对应测试：`tests/unit/test_gateway.py`（3 条 fallback）、`tests/unit/test_agent_permissions.py`（无身份拒绝）、`tests/integration/test_chat.py`（失败写审计）、`tests/unit/test_audit.py`（`test_write_failure_never_raises`、`test_anonymous_events_stay_in_memory_only`、有界性）。

#### Follow-up Questions

- #6 那条是什么？（**我的审查记录里第 6 条在这次提交里没有落地**——我不给它编一个修复内容。这条我会主动说，因为它正好证明「审查记录」和「修完」是两件事）
- 修完之后你怎么确认没漏？（跑全量 + 逐条问「这个修复有没有对应测试」。#7/#10 是清理类，我没有为它们写测试，因为我无法为死代码写测试——这也是诚实答案）

#### Pitfalls

- 不要把优先级讲成「安全 > 可靠性 > 性能」。我的判据是「错误是否被看见 / 是否必然发生」，这两条比类别标签更有说服力。
- 不要说 #4「导致过越权事故」。没有，它是**潜在**缺陷。

#### Interview Keywords

`silent model swap is the worst class` `fail-open in the auth layer` `must-happen beats might-happen` `every fix has a test`

---

## Q21-03 哪些是中低优先级？

#### Short Answer

#3（401 里列 token）、#8（429 没映射）、#7/#10（死代码）、#9（恒空字段）。它们的共同点是「不会造成错误结论」，但 #3 与 #8 是**形状错误**——留着会教坏后来人，所以我一并修了。

#### Standard Answer

**#3 401 details 泄露 token**：原 `DEMO_TOKEN_HINT = "、".join(f"{user.role}: {user.token}")` 会出现在 401 响应的 `details.demo_tokens` 里。这些是公开演示凭据，所以不是泄露**机密的事故**，但它是**「错误响应会告诉你该怎么绕过它」**这一类 API 设计缺陷的典型形状。修复后只保留角色名列表（`"、".join(f"{user.role}")`），把「怎么拿到 token」留在 README 与 DEMO_SCRIPT 里——**文档该说的不说成 API 义务**。
**#8 429 未映射**：`_CODE_BY_STATUS` 缺 `429`，所以任何 429 会被标成 `INTERNAL_ERROR`。这条特别值得讲：**我还没有 429 的生产者**（无限流代码），但契约层已经预留了错误码，映射缺失会让将来的第一个 429 直接归错类。修的是映射表（加上 `ERROR_TOO_MANY_REQUESTS`）。**「契约先行、实现后补」是可以接受的；「契约先行但契约本身错」不行。**
**#7 / #10 死代码**：`users.py` 里的无用分支、`AgentPlayground.tsx` 里一个恒真 className。删除，没有新增测试（死代码无法为它写有意义的测试；由 `ruff check` 与 423 测试保证没删掉行为）。
**#9 恒空字段**：`ChatResponse` 有 `sources: list[dict]` 与 `tool_calls: list[dict]`，但 `POST /api/chat` 走的是直连网关路径，**永远填不上**。
- 我当时的处理：在字段上写注释说明「chat 路径不填，供未来 agent-mode 统一响应使用」；
- 我复查后的判断：**这是次优的**。正确做法是要么删掉（本项目不需要向后兼容 —— 这也是我的项目纪律），要么让 `/api/chat` 在 `mode=agent` 时真的走 AgentService 并填上。今天它是个「引诱前端写错代码」的字段。**我把它作为 §22 待办而不是辩护对象。**

#### My Project Evidence

- `git show 460a6ee -- app/auth/dependencies.py app/api/errors.py`（两处小改动的 diff 很干净，适合现场给我看）
- `app/api/chat.py::ChatResponse`（那两个字段与注释）
- `tests/integration/test_rbac.py`（401 details 不再含 token 的断言）

#### Follow-up Questions

- 为什么不干脆删掉 `sources/tool_calls`？（应该删。我留着是**担心 Day 5 前端契约测试依赖它**，检查后发现不依赖 —— 属于「因恐惧而不作为」，我会直说这是我审查纪律不够狠的地方）
- 你怎么保证这类形状错误不再发生？（`[PRODUCTION_NEXT]` ① 响应模型字段与前端类型双向对齐检查（我有 TS 类型镜像 + 契约测试，但缺「未使用字段」检测）；② 把「每个响应字段至少一个消费者」列进 code review 清单；③ 上 vember/mypy 严格模式让 dead 分支更容易暴露）

#### Pitfalls

- 不要说「所有问题都修了」。#9 是**我明确留下的次优处理**，主动说出来反而证明我会自查。
- 不要把 #3 叫「安全修复」；叫「响应形状修复」。

#### Interview Keywords

`contract-level errors` `dead field I should have deleted` `documentation vs API obligation` `fear-driven inaction acknowledged`

---

## Q21-04 审查里最难发现的问题是什么？

#### Short Answer

最难的是「我自己这次修复引入的问题」。我在复查修复提交时发现了 #11：`460a6ee` 给 `ModelResponse` 加 `degraded` 字段时，把 `content: str` 写了两遍（重复声明），`ruff check` 抓不到、测试也抓不到。

#### Standard Answer

`[MY DESIGN]` 这条最值得讲，因为它说明**审查需要两轮**：第一轮审代码，第二轮审自己的 diff。
**发现过程**：我为了写这份面试材料重新通读 `app/gateway/base.py`，看到
```text
@dataclass(frozen=True)
class ModelResponse:
    content: str
    content:      # ← 重复声明（同类型，第二次是多余的一行）
    str
    model: str
```
（实际形态：`content: str` 连续出现两次）
**为什么没有任何机制抓到**：① Python 允许重复的类体注解，后一次覆盖前一次，frozen dataclass 的字段列表里只有一份 → **运行时行为完全正确**；② `ruff check`（E/F/I/UP/B）没有对该情形的规则命中（`F811` 管的是重新赋值/定义，注解重复不在其内）；③ 测试断言的是「有 content、值对、degraded 默认 False」，重复声明不改变任何断言。
**它有什么真实危害**：① 读者会疑惑「是不是有两个 content？」（我就疑惑了一次）；② 下一次有人复制这个类做变体时会照抄错误；③ 它是**审查提交本身**的产物，也就是说「我修 4 个缺陷时能引入 1 个新缺陷」——这个比例是我面试里最愿意说的自我认知。
**处理**：~~删掉重复行~~ **已删除**（最终一致性修复提交里 `app/gateway/base.py` 只保留一份 `content: str`；`ModelResponse` 的字段表与全部测试复核通过），并把 `git show <自己的提交>` 作为提交前的固定动作。
`[PRODUCTION_NEXT]` 我会补三条**自动化**：① 类型检查（mypy/pyright 严格模式能标出注解异常与冗余）；② 更宽的 ruff 规则集（`--select ALL` 跑一次看清单再挑，不是长期全开）；③ 一条「每个 diff 必须另一个人（或我第二天）看一遍」的纪律 —— 自动化替代不了时间距离。
**同类发现**：我复查时还确认了三处文档漂移——`README.md` 的测试数、`README` 里不存在的 `app/security/permissions.py` 路径（真实路径 `app/auth/permissions.py`）、`data/synthetic/README.md` 里写错的股票代码（应为 `301118.SZ`）。**这三处已在最终一致性修复提交里全部改正**（见 §34 的处置状态）。**文档也是代码**：如果不查，面试现场被问「你 README 里的数字怎么和跑出来的不一样」我就只能现编。

#### My Project Evidence

- `git show 460a6ee -- app/gateway/base.py`（证明重复声明由这次修复引入）
- 当前代码：`app/gateway/base.py::ModelResponse` 只有一份 `content: str`（重复行已删）
- 当前文档：`README.md` 测试数 = 实测 `423 passed`；权限路径已统一为 `app/auth/permissions.py`

#### Follow-up Questions

- 你还有什么没查到的？（**一定有**。我能说的是我查的手段有盲区：我没做过类型检查、没跑过依赖扫描、没在真实并发下压过、没有多浏览器验证过 UI。这五件事就是我下一步的审查手段）
- 怎么让第二次审查省力？（把 diff 当产品读：只看「这次改动让什么变成可能/变成不可能」，而不是重读整个文件）

#### Pitfalls

- 不要说「我审查很彻底所以没问题」。说「我的 diff 引入了 1 个新缺陷，我是靠再读一遍发现的」——这才是可信的自我认知。
- 不要把重复注解说成「严重 bug」。它是**噪音级缺陷**，价值在于它暴露了我的审查手段缺口。

#### Interview Keywords

`second-pass review of my own diff` `ruff can't catch everything` `docs drift is a real defect class` `fixes can introduce defects`

---

# 22 · 项目不足与下一步

## Q22-01 这个项目最大的不足是什么？

#### Short Answer

我会说三件，按严重度排：① 知识库没有文档级权限（ACL），所以它「安全」只在端点边界上成立；② 没有任何质量评测——我能证明行为不漂移，证明不了答案更好；③ 生产必需的能力缺了一整排（真身份、限流、重试/超时、审计不可篡改、备份与可观测到分位数）。

#### Standard Answer

`[MY DESIGN]` 我刻意不给「一个」答案，因为面试官问这题想看的是**我能否按严重度排序**，而不是能否自谦。
**① 文档级 ACL 缺失（我认为最严重，因为它与平台的定位矛盾）**
平台声称解决「企业权限与可追责」，但检索层不接收 principal、metadata 里没有密级。今天语料全公开所以无实际泄露，**但这是运气不是设计**。更糟的是：被污染的公开文档能影响所有人的回答（间接 prompt injection 的入口，见 Q17-02）。
修法（顺序即优先级）：metadata 落 `classification` + `allowed_roles/departments` → 检索**先过滤后排序** → 撤权失效通道 + 孤儿 chunk 对账 → **每条检索路径配负例测试**。
**② 没有质量评测（因为它让「效果」这件事我无法回答）**
我有 423 个测试，全部是关于**行为**的（拒答话术、引用字段、参数被拒、权限判定）。没有任何一个数字能回答「DeepSeek 和 Qwen 哪个在我们场景更准」。而 `EMBEDDING_PROVIDER=mock` 的检索效果**不能外推**。
修法：50–100 条自有题（与语料快照同 Git 版本）→ 规则判分优先（数字/引用/是否拒答）→ `recall@k` 与 `faithfulness` 两个基础指标 → 多 provider 对比矩阵。**一周能出第一版**，这也是我在 §12 计划里给恒光的第一件事。
**③ 生产必需面缺一大排（我会逐项给「为什么现在没有 + 什么条件触发我做」**
真身份/SSO（本期禁止，且我不该在 Demo 里连外部 IdP）、限流与配额（无共享计数器，所以我第一次真正需要 Redis）、per-tool timeout 与取消传播（只有 provider 60s）、重试与熔断（刻意不做，因为幂等未解）、审计不可篡改（普通可写 SQLite）、token/成本指标（`usage` 已透传但没聚合）、P95/P99（只有均值与峰值）、增量 ingest（只有全量重建）、持久会话与多轮记忆（messages 每次重置）、多副本与横向扩展（SQLite+Chroma 本地文件锁死单节点）、密钥管理/轮转（只有 env）、依赖与密钥扫描（无 CI 安全步骤）、类型检查（无 mypy/pyright）、前端 E2E（只有 API 契约测试）。
`[MY DESIGN]` 还有一排小的、我自己复查抓到的：**已修**的有 `AuditLog.clear()` 把有界 `deque` 换成**无界 list**（Fix #5 的反例，现已改为原地 `clear()` 并配回归测试，见 Q22-04）与三处文档漂移（§34）；**仍未修**的有 `ChatResponse` 的恒空字段（Fix #9 的次优处理）、`AuditAction` 声明了 3 个从未使用的动作常量（→ documents/audit/models 三处无留痕）、`permission_for_tool()` 的映射表和 `Tool.permission` 属性两处各写一次（漂移风险）、`app/services/chat_service.py` 是只剩一行文档字符串的死模块、（文档漂移三处——测试数、`app/security/permissions.py` 路径、合成数据 README 的股票代码——已在本轮一致性修复中改正，见 §34。）

#### My Project Evidence

- ACL 缺口：`app/rag/retriever.py`（`retrieve` 签名无 principal）、`app/rag/store.py::query`
- 评测缺口：全仓无评测/数据集目录；`app/embeddings/mock.py`（词面相似 ≠ 语义）
- 审计三常量未用：`app/observability/audit.py::AuditAction` vs `app/api/{audit,models,knowledge}.py`
- 权限双份定义：`app/auth/permissions.py::_TOOL_PERMISSIONS` vs 各 `Tool.permission`
- README 漂移：`README.md:21` / `README.md:49`
- 全量重建限制：`README.md` §已知限制（我自己写明的）

#### Follow-up Questions

- 只能修一件，你修哪件？（**文档级 ACL**，因为它同时收窄「越权读取」和「污染文档影响所有人」两条最坏路径，而且是接真实数据前的硬性门槛）
- 这些不足为什么不在 5 天里做？（有几件是 `[FACT]` SPEC 明确禁止扩张的（K8s/微服务/Redis/任意 SQL/控制类动作）；有几件是我判断 ROI 不够（评测集、熔断、类型检查），**我承认这个 ROI 判断是以「求职演示」为目标，不是以生产为目标**。这句区分很重要）
- 你会不会觉得这个 Demo 已经够「完整」了？（不会。我的判断是它「闭环完整、深度不足」：**边界正确，但没有一个数字能证明效果**。这句话我想让它成为我面试里的原话）

#### Pitfalls

- 不要说「没有大不足，都还行」。这题答砸比技术题答砸更致命。
- 不要把不足说成「时间不够」。要说「我做了范围决策，代价在这里，判据是 X」。
- 不要漏掉**小而具体**的不足（`clear()` 退化、恒空字段、双份权限定义）——这些细节的可信度远高于泛泛的「还可以更好」。

#### Interview Keywords

`ACL contradicts the platform's own claim` `no number can prove quality today` `boundary complete, depth missing` `closed-list self audit`

---

## Q22-02 如果多两周时间，你会先做什么？

#### Short Answer

按「一份投入同时降低风险与提高说服力」排序：① 检索层 ACL + 负例测试；② 评测集 + 规则判分 + 多 provider 对比；③ 增量 ingest + 一致性对账；④ token/成本指标 + per-tool timeout + 预算不等式；⑤ 类型检查 + 依赖扫描 + 密钥扫描进 CI。

#### Standard Answer

`[MY DESIGN]` 两周计划（每条都写清「完成判据」，因为没有判据的计划不是计划）：
**第 1 阶段（2 天）｜文档级 ACL**
`classification` + `allowed_roles/departments` 进 chunk metadata → `retrieve(..., principal)` → **先过滤再 top_k**（在 `store.query` 里用 where 过滤，避免「过滤后不足 top_k 又不补」）→ 撤权即重建该文档块 → **负例测试**：构造一份 manager-only 文档，断言 operator 的检索与 Agent 工具都拿不到它、且响应里不出现其标题 → 前端引用渲染按 ACL 走。
**完成判据**：负例测试全绿；把 ACL 字段删掉时至少一条测试变红（**能证明测试有效**，这是我会主动补的一句）。
**第 2 阶段（3 天）｜最小评测**
50–80 条自有题（三类：事实问答 / 结构化数据解释 / 必须拒答）→ 规则判分器（数字与被引片段求交、`document_id` 命中、是否出现「没有足够信息」）→ 输出 `recall@k`、`faithfulness@rule`、`refusal accuracy` → 用同一套跑 mock 与至少 2 个真实 provider → 一页对比表 + 一条回归基线（改 prompt/top_k 前后各跑一次）。
**完成判据**：能回答「top_k 从 5 到 8 时引用正确率变化多少」，且答案来自一次真跑，不是我的直觉。
**第 3 阶段（2 天）｜增量与对账**
`POST /api/knowledge/documents/{id}/refresh`（按 document_id 删旧块 → 重新分块嵌入，**单文档原子**）→ `GET /api/knowledge/reconcile`（文档清单 vs 索引，报孤儿/缺失）→ 重建改双索引 + 别名。
**第 4 阶段（3 天）｜生产必需面**
`observe_usage`（token 与估算成本，按 provider/model 分桶）→ per-tool timeout + 取消传播 + `TIMEOUT` 错误码 → 请求级 deadline 与「工具超时之和 ≤ Agent 墙钟 ≤ HTTP 超时」的断言测试 → 审计写**失败计数**指标（今天只有成功计数，见 Q22-04）→ `audit.read` 落审计（补上「看审计不留痕」）。
**第 5 阶段（2 天）｜工程护栏进 CI**
`mypy --strict`（先只跑 `app/`，把噪声列成 allowlist 而不是关掉）、`pip-audit`、`gitleaks`、`pytest --cov` 阈值、以及一条**lint 规则把我踩过的坑钉住**（例如禁止 `text(f"...")` 形式的 SQL）。
**剩余时间**：前端 E2E（Playwright 跑一遍 DEMO_SCRIPT 的六步，断言每个面板出现且引用可点）——因为契约测试钉住了字段但钉不住交互。
`[需要本人确认：这两周是否真能投入，还是必须在面试前只挑 1–2 件做完]` 如果只能挑一件，我挑**第 1 阶段**：它直接回应「你说的平台安全边界，做到了吗」。

#### My Project Evidence

- 落点明确：`app/rag/{retriever,store}.py`、`app/rag/ingest.py`、`app/observability/metrics.py`、`app/agent/executor.py`、`tests/`
- 已有可复用的地基：`allowed_tool_names()`（裁剪工具集只要接到 loop）、`usage` 已在 `ModelResponse`、错误码与信封可扩展（加一个 `ERROR_TIMEOUT`）、`_require_content` 已示范「平台状态用 409」
- 已验证的测试风格可延续：`tests/integration/test_web_console_contract.py`（30）作为「字段契约」范式，加 ACL 负例是同一手法

#### Follow-up Questions

- 为什么评测排在 ACL 之后？（**因为没权限的评测结果在生产里是不能用的**：先证明「不该看的看不到」，再谈「看到的答得好」。顺序本身就是我的判断）
- 为什么不上 rerank/混合检索？（评测出来后才知道缺什么。在没有指标之前调检索参数，只是把我的直觉换了一种写法）
- 两周之后还缺什么？（多租户、真 SSO、异步审计落盘、备份演练、UI 降级横幅。我会说「还缺很多」并给**判据**：什么时候那些变成必须做——一旦有非公开数据入库）

#### Pitfalls

- 不要给一个「什么都做一点」的清单；每条要有完成判据与顺序理由。
- 不要承诺「两周做完」而忽略 `[FACT]` 这是一个求职 Demo（面试官问「那你怎么还没做」时，正确答案是「这是我为入职后前两周准备的方案，见 §11 的分阶段落地」，或诚实说「我按 5 天的求职目标做的范围，代价在这里」）。

#### Interview Keywords

`ordered by risk-per-day` `tests that fail when the guard is removed` `measure before tuning` `done criteria per item`

---

## Q22-03 生产环境还缺什么？（完整清单）

#### Short Answer

一张表说完，分六类：身份与授权、可靠性、可观测、数据与治理、部署运维、质量工程。每类我给「缺什么 + 什么时候必须补」。

#### Standard Answer

| 类别 | 缺什么 | 触发补做的条件 |
|---|---|---|
| **身份与授权** | SSO/OIDC 或 LDAP；会话与 token 生命周期（短时效 + 刷新 + 撤销）；多租户/组织维度；文档级 ACL；operation 级权限；撤权即时生效 | 有任何非公开数据入库的**第一天** |
| **可靠性** | per-tool/per-provider timeout + 取消传播；请求级 deadline 预算；只读重试 + 退避 + jitter；熔断；限流与配额；幂等键与对账（写操作时）；优雅停机（在途请求完成）；多副本 + 负载均衡 | 用户超过 ~30 人，或接入任何真实业务系统 |
| **可观测** | token/成本指标与按部门归因；P95/P99 延迟（直方图）；OTel tracing（跨服务边界）；审计写**失败**计数 + 告警；质量看板（拒答率、空召回 top query、引用一致率）；SLO 与告警规则 | 上线当周（成本与告警）；拆服务之前（tracing） |
| **数据与治理** | Postgres（含审计独立库/独立账号）；向量库高可用与备份；增量 ingest + 双索引别名 + 孤儿对账；数据分级与保留期策略；备份**恢复演练**；密钥管理/轮转 | 真实数据接入前（分级、备份）；审计进合规流程时（不可篡改） |
| **部署运维** | 镜像 registry + tag 策略（sha + 语义版本）+ 扫描；CI（测试/ruff/类型检查/密钥扫描/依赖扫描）；环境隔离（dev/stage/prod）；配置与特性开关；发布与回滚脚本；容量基线与压测报告；TLS 与网络边界 | 有第二个「环境」时就需要 CI（否则我不知道 prod 上跑的是什么） |
| **质量工程** | 评测集 + 判分 + 基线（Q22-02 第 2 阶段）；对抗/prompt-injection 测试集；前端 E2E；契约测试扩展到「未使用字段检测」；数据迁移脚本与回滚测试；混沌/故障演练（provider 挂、DB 慢、Chroma 不可用） | 每次 prompt/模型变更前（评测）；每次接入新外部系统前（故障演练） |
**我会特别强调这三条容易被漏的**：
① **审计写失败的可见性**——只有成功计数的审计指标是自欺；② **备份恢复演练**——没演练过的备份不算备份，这条我在恒光的语境下尤其想讲（安全场景的制度就是靠演练活着）；③ **评测与语料同版本**——不然分数不可比，而「不可比的分数」比没有分数更有害（它会让人以为在进步）。

#### My Project Evidence

- 现状基线可指：`app/observability/metrics.py`（15 项，无成本/无分位数/无失败计数）、`docker-compose.yml`（单节点、无 registry）、`pyproject.toml`（无 CI 配置文件在仓库里、无 mypy）、`README.md` §已知限制

#### Follow-up Questions

- 这十几件事你先做三件？（① SSO + ACL；② 超时/取消 + 一个能告警的失败计数；③ 评测集 + 成本归因。理由依次是：不做就进不了企业；不做就无法运维；不做就没法证明换模型是对的）
- 哪些永远不该由这个平台做？（**任何控制类动作**、任何业务系统写操作的第一期、任何替代审批流程的自动放行、任何把内部数据外发到云端的默认行为）

#### Pitfalls

- 不要把「生产还缺什么」答成「加 K8s 加 Kafka 加 Redis」。要说清**每个组件被什么需求触发**（我的 Redis 触发条件是共享计数器，见 §5 Q5-12）。
- 不要说「上生产只差一点」。要说「差一个数量级的运维面，但形状已经对了」——这个区分是成熟度信号。

#### Interview Keywords

`six-category gap list` `trigger conditions not tech bingo` `untested backup is not a backup`

---

## Q22-04 有哪些你自己还没解决的已知问题？

#### Short Answer

有一份我自己复查出来的 8 条具体清单（含文件行号级定位），其中两条是我审查修复那次提交**自己引入/自己留下的反例**。

#### Standard Answer

`[MY DESIGN]` 这份表是我打算在面试里作为「我对自己代码的信任度校准」来用的——**每条都可当场指出**：
| # | 问题 | 位置 | 后果与我的判断 |
|---|---|---|---|
| 1 | ~~`ModelResponse.content: str` 重复声明~~ **已修** | `app/gateway/base.py` | Fix #2 引入、本轮删除。运行时行为本来就正确，但它是噪音且 `ruff check`/测试都抓不到 → 说明我缺类型检查（Q21-04） |
| 2 | ~~`AuditLog.clear()` 把有界 `deque` 换成**无界 list**~~ **已修** | `app/observability/audit.py::clear` | **Fix #5 的反例**。现改为原地 `self._records.clear()`（保留 deque 与 maxlen），并新增 2 条回归测试钉住这个约束 |
| 3 | 审计只有 `audit_write_count`（成功），**无失败计数** | `app/observability/metrics.py` | 写失败只落 `last_error` + warning。审计系统自己「悄悄少记」是不可接受的不可见性 |
| 4 | `AuditAction.KNOWLEDGE_DOCUMENTS / AUDIT_READ / MODELS_LIST` 声明未使用 | `app/observability/audit.py` | 三个只读端点无留痕；「看审计不留痕」这条链断在这儿 |
| 5 | 工具权限映射**两处定义** | `app/auth/permissions.py::_TOOL_PERMISSIONS` vs 各 `Tool.permission` | 加新工具可以只改一处 → 静默漂移。正解：由 `Tool` 派生，删掉手工表（`[PRODUCTION_NEXT]`） |
| 6 | `ChatResponse.sources / tool_calls` 恒空 | `app/api/chat.py` | Fix #9 我只加了注释没删字段（Q21-03）。引诱前端写死代码 |
| 7 | `app/services/chat_service.py` 是**只剩文档字符串的死模块** | `app/services/chat_service.py` | 72 字节。应删。留着说明我没有「清理未使用模块」的自动检查 |
| 8 | 文档漂移：README 测试数、`app/security/permissions.py` 不存在的路径、`data/synthetic/README.md` 股票代码 `301109.SZ` | 3 个文件 + `seed.json` | **已全部修正**（本轮一致性提交）。它们原本是事实性错误，全是可能被当场翻开的东西 |
`[MY DESIGN]` 我会用一句话收：**「#1、#2 是修 bug 引入的，#8 是文档不跟随代码，#3、#4 是观测与审计的自指缺口。这四类的共性是：它们都不会让任何测试变红。」** 所以我的对策不是「更细心」，而是**加机制**：类型检查、约束旁路的负例测试、以及把文档当产物校验（例如测试里断言 README 声明的测试数与实际收集数一致——这个断言很便宜，我打算加）。

#### My Project Evidence

#1、#2、#8 的「已修」可当场指出：`grep -c "content: str" app/gateway/base.py` → 1；`grep -n "_records.clear()" app/observability/audit.py`；`tests/unit/test_audit.py::TestMemoryBound`；文档侧 `grep -rn "app/security\|301109" README.md data/` → 无匹配。#3–#7 仍可指位置（上表第三列），另有 `uv run pytest -q` → `423 passed` 与 `README.md` 对照。

#### Follow-up Questions

- 那你为什么不现在就修完？（#1/#2/#3/#4/#7/#8 是 30 分钟工作量，我打算在面试前把它们提一个 `fix: address self-review findings` 提交，并配对应测试；#5/#6 需要设计决策（派生映射 vs 双写校验、字段删除 vs 语义填充），我不想在没有测试护航的情况下顺手改。**这个「哪些立刻改、哪些要先加测试」的区分本身就是答案**）
- 你还怀疑哪些没查到的地方？（并发：`AuditLog` 的 deque 在多线程下我依赖 CPython 语义而不是显式锁；Chroma 多进程访问；nginx `client_max_body_size` 默认 1m 对 PDF 上传是否够；前端在慢网络下的重复提交防护。这四个是我现在**没有证据就说没问题**的地方）

#### Pitfalls

- 不要临场编「还有一些小问题吧」。有清单就说清单，一条一条来。
- 不要把 #8（文档/代码漂移）当成不重要的细节——它是面试官**最容易自己发现**的一类问题，先说出来就是主动权。

#### Interview Keywords

`self-review has line-level evidence` `two defects my own fix introduced` `mechanisms not care` `doc drift is a defect class`
# 23 · 最容易被质疑的 9 题

> 这节是「高危题」，共 9 道 + 1 张速记表。它们危险的原因都一样：**我说的每句话都来自一个求职 Demo**，而面试官知道这件事。
> 共同纪律：先给**事实边界**，再给**技术判断**，最后给「我会怎么补」。三段不能调换顺序。

### Q23-01 「你这个项目是 AI 写的吧？」

#### 为什么危险

423 个测试、5 天做完、7645 行 Python + 3133 行 TS + 4 份齐全文档——这个组合**本身就招问**。

#### 标准答案（照此说）

「我用了 AI 辅助工具，我不否认，也讲清楚它在里面的角色。`[需要本人确认：如实说明使用的工具与范围]`
它帮我做的是：查 API 细节、生成样板代码、在我卡住时给候选实现、提醒边界情况。
它没做的是：定架构边界（网关只一个出口、工具只白名单、权限分两族、审计不记 prompt、fallback 默认关闭，这些是我定的）；定位并修掉审查里那 9 项缺陷；以及**每一个我现在能当场指给你看的行为**。
如果我离开这套代码，我现在可以**现场演示三件事**证明这是我的代码：① 改 `LLM_FALLBACK` 并解释为什么默认 false；② 加一个 `equipment_lookup` 工具（继承 `BusinessQueryTool`，只要一个 operations 字典，§8 讲过）；③ 讲清 `ToolExecutor` 为什么先判未认证再判角色权限。」

#### 加分动作

- 主动提 `git log`：**7 个提交按 Day 1–5 递进，每次都有可运行的测试增量**（`1ae952d` Day1 → `460a6ee` Audit Fix）。AI 一次性生成的东西**没有这种提交历史**。
- 主动提我复查发现的 8 处残留（§22 Q22-04）——一个「生成的代码」不会有带自我否定的清单。

#### 不要说

「不是 AI 写的」（一旦被追问细节就全盘崩坏，且构成不诚信）；「AI 写的又怎样」（态度问题）；超过 40 秒的工具链讲解。

---

### Q23-02 「5 天做完这么多，是不是每样都只做了一层皮？」

#### 标准答案

「每样都只有一层——**这是我刻意选的**。我要的是每条主链路端到端跑通、边界正确，而不是把某一个模块做深。
验证「这层多薄」的方式：① 423 个测试不是快照测试，它们断言的是**行为**（越权必须拒绝、无依据必须拒答、降级必须打标、mock 失败不再降级、参数越界必须变成受控失败）；② 我能当场列出**没做什么**：没有 rerank、没有 BM25 混合检索、没有会话记忆、没有流式输出、没有 per-tool timeout、没有增量 ingest、没有文档级 ACL、没有成本指标、没有评测集——这 9 条我写在 §22 里。
所以准确说法是：**边界是完整的，深度是单层的**。我把它当地基不当成品。如果它只是皮，那它连皮的功能都过不了自己的测试——我特意让测试覆盖失败路径，不是只覆盖 happy path。」

#### 加分动作

指出两个「只有真做过才会留的痕迹」：① `app/api/router.py` 注释解释了为什么路由装配不能放进 `app/api/__init__.py`（循环导入）；② nginx 用变量 + 内嵌 resolver（`host not found in upstream` 我踩过）。这两处是**踩坑成本**，不是生成成本。

#### 不要说

「我效率很高」（引战）；「demo 嘛」（贬低自己）。

---

### Q23-03 「你们这个 ERP 数据是哪来的？接的什么系统？」

#### 必须一字不差的诚实

「**没有接任何真实系统**。`data/synthetic/` 是我按硫氯产品链的**结构**人工构造的合成数据：8 家供应商、10 种物料（原盐、盐酸、液碱、硫酸、氯酸钠这类）、约 328 张采购订单、9 条库存快照、安全事件、设备与维修记录。`data/synthetic/README.md` 第一行就写了它与公司真实经营数据无关，供应商名和价格都是虚构的。
所以准确说法是：我实现的是**接口的形状**——固定 operation、参数化查询、双视图输出、工具级权限、每次调用落审计。我**没有**真实 ERP 的对接经验，也不假装我有。
如果我入职去做这件事，我的第一步不是写代码，是三件确认（§9 Q9-06）：谁是数据 owner、能不能给我预授权的只读视图、口径争议谁裁决。」

#### 为什么这样答

这题真正的考点是「**候选人会不会把没做过的事说成做过**」。一个假的「我们接的是用友 U8」能骗过这一问，但会在第二问（表结构、单据状态机、审批字段）被拆穿，代价是整个面试的可信度。

#### 加分动作

把话题引回设计：「结构像」是有价值的——物料口径来自公开年报的产品链描述（`[FACT]` 见 §35），所以 Agent 回答出来的采购结构看起来合理。这是我做合成数据时唯一追求的逼真度，不是数字。

#### 不要说

「差不多就是个真 ERP」（**绝对禁止**）；任何暗示接过某个 ERP/OA 品牌的品牌名。

---

### Q23-04 「你为什么不直接用 Dify / RAGFlow？人家两天就搭出来了。」

#### 标准答案

「两天搭出来的是**应用**；我要交付的是一层我能对每一行负责的**边界**。
三个具体差别：① Dify/RAGFlow 的知识库权限、检索排序、prompt 组装由它决定，而我演示的恰恰是这些决策（比如检索的「先融合打分、再截 top_k、再 min_score 过滤」这个顺序是我选的）；② 我的审计净化策略（denylist + 只留长度 + 截断 160 + 不记 prompt）在生产里是要被合规审的，我没法把它交给一个我看不见的黑盒；③ 我要能回答「工具越权为什么不是 403」这种问题，用现成产品我答不了实现层。
**但我不认为答案永远是自研**。我的判断标准（§28 Q28-01 那张 8 维问卷）：如果一个现成组件解决的正是我的瓶颈、且它的边界我能审计，我就用它。向量库我用 Chroma 而不是自己写 HNSW；embedding 我接 OpenAI 兼容端点。**我不选 Dify 不是它不好，是它好的地方不在我要练的肌肉上**。」

#### 加分动作

给出「入职后发现公司已经上了 Dify」的应对：那我退到平台层该做的事——身份接入、ACL、审计外送、模型网关统一出口、评测与成本治理，把 Dify 当成平台上的一个消费方。**这句话能挡住 90% 的「你是不是只会造轮子」。**

#### 不要说

「那些都是玩具」（傲慢 + 暴露没评估过）；「我会用，只是这次没用」（没有细节等于没答）。

---

### Q23-05 「RAGFlow / FastGPT 的检索效果比你好，你怎么比？」

#### 标准答案

「**很可能在公开基准上它们确实更好，我不争**。直接原因：我默认 `EMBEDDING_PROVIDER=mock`，是 CJK 字符 bigram 哈希进 1024 维的词面相似向量，**没有语义**。而 RAGFlow 这类产品的核心之一就是真实 embedding + rerank + 版面解析。我拿什么赢？不拿这个赢。
所以我的回答分两半：
① **承认**：我的检索质量数字为零——我没有评测集（§22）。任何人拿真实 embedding + rerank 的召回率跟我的 hash-ngram 比，我输。
② **换题**：这三类产品解决的是「一套能用的 RAG 应用」；我要解决的是「这条链的**治理**」：谁能检索到什么（ACL）、答案依据哪份文件哪一版（引用 + `published_at`）、模型能不能表达「写」（operation 白名单）、越权与降级有没有痕迹（审计 + `degraded`）。**这两件事不冲突，而且真上线时都要做**。
③ **我怎么做选型**（§28 Q28-01/Q28-02）：先建自有评测集（与语料同版本）→ 候选组件同题跑 → RAGFlow 的召回/忠实度显著更好**且**它的权限模型能接进我们的身份体系，我就用它做检索、把平台层做在它外面；接不进去，就只借它的解析与 rerank，或自建。
**结论：效果我不能跟你比，判据我能给你。**」

#### 加分动作

自曝一处真实短板：「我的 chunker 会把 Markdown 表格切成一行行 `|`（§7 Q7-03），设备手册和参数表密集的场景会先在这里掉质量。这是我列在待办里的。」

#### Pitfalls

不要说「差不多」或引用任何编造数字；不要贬低产品（尤其公司可能已在用某个）。

---

### Q23-06 「one-api / new-api 已经解决模型网关了，你重写一遍的意义？」

#### 标准答案

「如果公司已经有一个 one-api，**我会把 `OpenAICompatibleProvider` 的 base_url 指过去，然后删掉我自己那 60 行网关代码**。这不是认输，这是它的正确用法：我的抽象是「业务代码只走一个出口」，出口后面是进程内 router 还是外部服务，是部署决策，不是契约决策。
差别在哪：one-api 是**独立进程 + 独立运维面**，它擅长渠道管理、令牌分发、计费、多模型故障转移。我这个是**进程内一层**，它做 one-api 做不了的那部分：把「降级要打标（`degraded`）」带到 `ModelResponse` 让 Agent loop 能分支；把 provider/model 名写进审计行；在出口前拦参数校验；让 423 个测试零网络可跑。
`[PRODUCTION_NEXT]` 我心中的生产组合：**one-api 负责渠道与配额，我这一层负责语义契约**，两者不互相替代。所以如果你意思是「你是不是重复造轮子」，我的答案是：在这个 Demo 的范围里，我造的这一段（语义契约）轮子上没有；在生产里我会把渠道那一层让给专门的轮子。」

#### 加分动作

给一句可当场验证的话：「你可以现在就查：`LLM_PROVIDER=openai-compatible LLM_BASE_URL=... LLM_API_KEY=...`——如果我把 `BASE_URL` 换成你们 one-api 的地址，我的代码一行不用改。」

#### Pitfalls

不要说「one-api 功能不够」（它功能很多，只是不同层）；不要承认「我不知道有 one-api」。准确说法：「我知道，我在我的目标下选择不把它拉进本地依赖」。

---

### Q23-07 「你连化工专业都没有，安全场景怎么做？」

#### 标准答案

「**专业判断我不做，也绝不应该由我做**。我能做且应该做的有三件：把专业判断**结构化地记录下来**、把**责任链**在系统里保住、把**边界**做硬。
具体：① 记录 = 检索与引用必须能到「哪份制度、哪一条、哪一版、什么时候生效」，安环专家 10 秒能判断对不对（我的 `title/section/page/published_at/url` 就是为这个）；② 责任链 = 审计保留「谁用哪个模型问了什么、拿到了什么建议」，AI 给的建议必须有一个**责任人字段给人填**；③ 边界 = 我的工具面里**根本没有**控制类动作，只有只读查询与分析，因此不存在「模型给错处置建议并被执行」的路径。
我靠的是流程不是知识：**领域专家是平台的验收者，不是平台的用户之一**。这与 JD 第 6 条（§2 顶部）是同一件事。
同时我承认：看不懂工艺、读不懂 P&ID、不知道 HAZOP 怎么开——**这些要么学，要么靠专家**。我不会因为不懂就把它做成通用问答机器人，那才是真危险。」

#### 加分动作

准备一个「快速补领域知识」的真实方法（`[需要本人确认：举一个自己速成陌生领域的例子]`），并说明我会把领域知识需求写成问题清单去问安环部，而不是自己猜。

#### Pitfalls

不要显摆化工术语（错一个就完）；不要说「技术上差不多，行业知识可以学」——太轻。

---

### Q23-08 「你没真正上线过系统，怎么保证写得出来到生产的东西？」

#### 标准答案

「**我不能保证。这个问题我只有一个诚实答案：我保证的是我知道自己在哪些地方没把握**（§22 Q22-03 那张表）。
我能提供的证据是**判断质量**，不是运维履历：① 我刻意保留了可运维的东西——结构化日志、`request_id` 全链、`/health` 探针、`/metrics` 计数器、统一错误信封、失败路径的审计；这些不是功能，是运维者会感谢的东西。② 我能说出**为什么某处会在生产出事**：审计写失败只有成功计数（§22 Q22-04 #3）；同步 SQLAlchemy 放在 async 路径里（§5/§19）；`AuditLog.clear()` 把有界 deque 换成无界 list（§22 Q22-04 #2）；nginx 没设 `client_max_body_size`（§18）——**能预测自己代码怎么坏，比宣称它不会坏更接近可信**。
`[需要本人确认：如果有真正负责过上线/运维的系统（哪怕小项目），这里换成那个真实例子]`。如果没有，我就按上面这套答，不虚构值班与事故。」

#### 加分动作

给一个「入职第一个月」的运维动作清单：备份+恢复演练、告警规则（provider 错误率、审计写失败、P95、空召回率）、发布与回滚脚本、变更需评审的清单。**这比任何形容词都像一个运维者。**

#### Pitfalls

不编造生产事故经历；「我学习能力强」不是答案。

---

### Q23-09 「你这项目里为什么有死模块和恒空字段？」

#### 标准答案

「因为我在 Day 4 做过一次重构，**留下了重构的尸体，而我没有清理它的机制**。
两处：① `app/services/chat_service.py` 现在只剩一行文档字符串——它曾经是 `/api/chat` 的服务层，我把 chat 路径改回直连网关后没删文件；② `ChatResponse` 的 `sources`/`tool_calls` 在 chat 路径恒空——是我 Fix #9 时选了「加注释说明」而不是删除（§21 Q21-03）。
当时没删的理由：**怕 Day 5 的前端契约测试依赖它**。查过之后确认不依赖，那就是**因恐惧而不作为**。这是我自己复查时记下的判断错误，不是遗留的惊喜。
正确处理：`chat_service.py` 直接删；`ChatResponse` 要么删字段，要么让 `mode=agent` 真的走 AgentService 把字段填上——**留一个空壳字段等于给前端埋坑**。
我也不会为了显得干净只承认这两处：同类问题我列了 8 条（§22 Q22-04），包括 README 的测试数、`app/security/permissions.py` 这个不存在的路径、`data/synthetic/README.md` 的公司代码——**这三处文档漂移和其中两处代码缺陷（重复字段、`clear()` 退化）我已经改掉了**。**它们都是「不会让任何测试变红」的缺陷，所以对策不是更细心，是加机制：类型检查、未使用字段检测、文档断言测试。**」

#### 加分动作

现场提议加一条测试：断言 README 声明的测试数 == `pytest --collect-only` 的收集数。**用一条测试把「文档漂移」钉住**，是这题最漂亮的动作。

#### Pitfalls

不要说「小问题不重要」（它们重要，因为我承认了它们的类别）；不要说「都是 AI 带进来的」（责任在我）。

---

### Q23-10 高危题小结（面试前 10 分钟过一遍）

| 题 | 我的第一句（背这个） |
|---|---|
| 是 AI 写的吧 | 「用了辅助工具，我不否认；证明这是我的代码，方式是你挑一个让我现场做」 |
| 只做了一层皮 | 「边界完整、深度单层，是我为这个目标刻意选的；9 条『没做』我列在 §22」 |
| ERP 哪来的 | 「没有接任何真实系统。我实现的是接口的形状」 |
| 为什么不用 Dify | 「它好的地方不在我要练的肌肉上；判断标准是一张 8 维问卷，不是产品名」 |
| 检索比不过 RAGFlow | 「效果我不跟你比，判据我能给你：自有评测集 + 同题对比」 |
| one-api 已解决 | 「我把 base_url 指过去删掉自己那层；我造的是它没有的语义契约」 |
| 没化工背景 | 「专业判断我不做；我结构化记录判断、保住责任链、做硬边界」 |
| 没上线过 | 「我保证的是我知道自己在哪没把握；我能预测这套代码怎么坏」 |
| 死模块/恒空字段 | 「重构的尸体 + 我没清理它的机制；对策是加机制不是加细心」 |

---

# 24 · 遇到不知道的问题怎么回答

### Q24-01 通用模板（四步）

#### Short Answer

**界定我知道的 → 说出我不知道的具体是什么 → 给推理方向与判据 → 说我会怎么查证**。绝不空投降伏，也绝不硬编。

#### 标准答案（可背的四句结构）

1. 「**这块我没做过 / 这个细节我不确定**」——先给结论，不要绕。绕了三句再承认，可信度已经没了。
2. 「**我不确定的是具体哪一点**」——把边界划准：「我知道 X 与 Y，不确定的是 Z」。这一句让「不知道」变成有知识的。
3. 「**按我理解的原理，我会这样推**」——推理说出口并标注是推演：「如果它遵循 … 的一般设计，那么 …；不遵循，我的结论就错」。
4. 「**我会这样查证**」——路径与时间：查官方文档 X 章 / 起最小复现 / 在评测集上跑一次 / 问数据 owner。
**结尾主动给替代贡献**：即使这题不会，我也能说一句相邻的、我有把握的（被问 pgvector 索引参数不会，但「我们的规模下向量库不是瓶颈，ACL 与增量重建才是我该担心的」我有把握）。

#### 变体 A：完全没听过的名词

「这个名词我没听过。**你能给我一句它的定位吗？**我保证不复述你的话当答案，但我大概能马上告诉你它和我哪块经验相邻。」——**反问是被允许且专业的**；装作听过再编，是唯一不可接受的做法。

#### 变体 B：被问公司/业务事实

「我不知道恒光内部现在用什么系统、有什么数据、谁负责哪块——我只有公开资料。我能说的是：如果要做 X，我第一步会确认 A、B、C。」**永远不要把 `[INFERENCE]` 说成 `[FACT]`**（§0.2 第 3 条纪律）。

#### 变体 C：只记得一半的技术细节

「我记得 A 与 B 的关系，不记得具体参数名/默认值。我不猜参数名，因为它会误导你。」——**明确拒绝编造**比给出一个可能对的答案更能建立信任。

#### Pitfalls

不用「这很简单/其实不难」开头然后讲错；不混三档表述（读过 ≠ 用过 ≠ 上线过）；同一模板不连用超过三次——如果一场面试有四次「不知道」，收尾要诚实：「我今天有 X 处答不上来，共同点是我确实没在生产碰过这块。我没法在面试里补上，但我能给你我入职后的学习顺序。」

---

### Q24-02 被追问到自己代码边界之外

#### Short Answer

承认「这段代码里没有那个东西」，然后把话题从「能力」转到「设计意图 + 我会怎么改」。绝不虚构实现。

#### 标准答案（三类情形）

① **「你的 X 是怎么实现的？」而它根本没实现**：「没有实现。今天的行为是 Y（可指代码），X 是缺口，记在我的待办第 N 条。如果现在要我设计：…」。
**我预期最可能被问到的 7 个「没有」**（被问到任何一个都能立刻报出它在 §22 里排第几）：per-tool timeout、流式输出、会话记忆、P95 分位数、成本归因、文档级 ACL、增量 ingest。
② **「你为什么不用 X 方案？」**：判据 + 代价 + 切换条件。「我用 A 因为约束是 C；代价 D；当 E 发生时换 X」（例：SQLite→Postgres 的切换条件，§20 Q20-02）。
③ **问到自己也没想清楚的**：「这个我没想清楚。我现在的假设是 A；验证它的方式是 B。**你如果有经验，我很想听你说这里通常踩什么坑。**」——把未知变成真实的请教，往往能拿到对方对岗位的真实期待。

#### Pitfalls

最坏情形：把设计说成实现（例如把 §10 的 MCP 方案说成「我们已经接了」）。追问一次细节就崩，崩的是整场面试；「这个看具体场景」必须紧跟一个具体判据，否则就是空话。

---

### Q24-03 「我不能说」的红线清单（6 条）

| 红线 | 为什么 | 正确说法 |
|---|---|---|
| 声称接过真实 ERP/OA/DCS | 细节追问即崩 + 不诚信 | 「实现的是接口形状，数据是合成的」（Q23-03） |
| 声称有化工行业经验 | 同上 | 「没有；我的价值是把领域判断结构化并保住责任链」（Q23-07） |
| 引用任何编造数字（准确率/QPS/用户量/成本/榜单） | 无法自证 | 只报本仓库可查的数字（§27 数字卡） |
| 说恒光内部有什么系统/在做什么 AI 项目 | 我没有这个信息 | 标 `[INFERENCE]` + 「入职后需核实」 |
| 前雇主内部数据、代码、客户名、同事隐私 | 违约 + 不专业 | 只讲公开技术栈与我承担的职责类型 |
| 承诺我无权承诺的事（到岗日、薪资让步、上线时间、任意驻场） | 先松口 = 事后失信 | 「我今天可以确认 X；Y 需要 …」 |
外加一条易被忽略的：**「读过某产品文档」≠「评估过某产品」**。可以说「我读了 X 的架构文档并跟我的实现对比了这几个维度」——给方法与结论，不给身份。

---
# 25 · 行为面与情境题

> 纪律：本节所有涉及真实雇主的例子一律 `[需要本人确认]`。模板部分只用**本仓库可验证的事实**（提交历史、审查记录、SPEC 范围决策），这些是我现在唯一能负责任地讲出来的「行为证据」。

## Q25-01 讲一个你解决过的最难的技术问题。

#### Short Answer

用「审计写失败会不会把主请求打挂」这条链：从一次自查发现问题，到把它复现成失败测试，到修完留下回归保护——三步完整，全部可指代码。

#### 标准答案

`[MY DESIGN]` 我把问题定义成三层，而不是一行代码：
① **现象**：审计写入路径如果抛异常，业务请求会被一个「本该是旁路能力」的东西打死。这在企业平台上是**结构性**问题：审计越重要，它越不该有能力阻断服务。
② **矛盾**：但反过来，「审计静默失败」更糟——你会得到一个「看起来什么都记了」的系统。所以正确答案不是「吞异常」，而是**吞异常 + 让它可见**。
③ **实现**：`AuditLog.record()` 里 `except Exception` → 存 `_last_error` → `logger.warning(extra={event:"audit.write_error", action, error_type})` → 返回事件（请求继续）。同时 `test_write_failure_never_raises` 把这条语义钉住；`test_anonymous_events_stay_in_memory_only` 钉住另一条相关约束（`user_id NOT NULL` 的表契约不能被匿名事件破坏）。
**我最后又推翻了自己一点**：复查时发现「可见」这一半**还没做完**——`metrics` 里只有 `audit_write_count`（成功计数），**没有失败计数**。所以我今天的答案里明确带着这条：旁路能力失败必须是可告警的一等指标，不是日志里的一行 warning（Q22-04 #3）。
**这道题我想展示的不是「我修了个 bug」，是「我能把一个工程判断拆成现象/矛盾/实现/残留四步，并且记得自己没做完什么」。**

#### My Project Evidence

- `app/observability/audit.py::record`（含 `db.is_initialized` 前置检查、`except Exception` 分支、`_last_error`）
- `tests/unit/test_audit.py::TestResilience::test_write_failure_never_raises`
- 残留缺口：`app/observability/metrics.py`（无 `audit_write_failure_count`）

#### 如果面试官追问「那生产上你怎么做」

`[PRODUCTION_NEXT]`：审计写失败要分级——**关键动作（ingest / 权限变更 / 未来的写操作）失败应让请求失败**（fail-closed），只读旁路可以降级但必须计数 + 告警 + 本地暂存重投（outbox）。我现在对全部事件一律「不阻断」，是一个简化的统一策略，我会说清这一点。

---

## Q25-02 讲一次你和自己（或团队）的意见冲突。

#### 标准答案（没有真实团队冲突时用这个版本）

「我没有可以举的真实团队冲突案例——这个项目只有我一个人。但有一次**跟自己旧判断的冲突**我可以讲，因为它同样是决策成本。
冲突点：**Agent 的工具越权该不该返回 403**。
- **我最初的设计直觉**：越权就是 403，天经地义，这也是我 Day 3 写 executor 时的想法。
- **让我改判据的事实**：Agent 的一次运行里，用户的问题是合法入口（他有 `agent:run`），是**模型**替他选了一个不该用的工具。如果这时抛 403，用户看到的是一个失败页，什么也拿不到；而实际上「模型试图越权、被平台拦住」这件事**恰恰是最需要被记录而不是被中断**的信号。
- **我最后定的规则**：Agent 运行整体返回 200，工具项带 `error_code=PERMISSION_DENIED`，答案里明说「这个数据你没有权限」；审计同时记 `tool.call=denied` 与 `agent.run`（若全部工具调用都被拒且无成功 → 整条 `denied`）。也就是把「协议层的正确」与「业务层的正确」分开满足。
- **代价我也认**：这会让「HTTP 状态码」失去一部分监控意义，所以我必须让 `permission_denied_count` 和 `error_by_code` 来补位。这个代价我写在指标层里了。
**结论**：我的原则是「**判据来自约束，不来自直觉；改判要付代价，代价要显式记账**」。」

#### Follow-up 准备

- 如果面试官说「我们那边会要求 403」：「那我照你们的标准改，但会保留 `denied` 审计 + 独立错误码，并且把「Agent 整体失败 vs 局部无权限」在 UI 上分开显示——因为这两个对用户是完全不同的经验。」

#### Pitfalls

- **绝不虚构与同事/上级的冲突**。`[需要本人确认：如果有真实案例，用真实案例替换本题]`

---

## Q25-03 你如何在信息不全的情况下做决策？

#### 标准答案

「我在这个项目里做的就是这件事——我对这家公司的全部了解只有一篇 JD 加公开资料。我的做法有四个动作，我认为它们是通用的：
① **把不确定的东西显式贴标签**。这份面试材料里我用了五类标记：`[FACT]`（附来源与检索时间）/ `[INFERENCE]`（推演）/ `[MY DESIGN]`（可在代码验证）/ `[PRODUCTION_NEXT]`（建议，不是现状）/ `[需要本人确认]`（涉及个人信息我不代填）。**标签是给自己用的纪律工具**：写了 `[INFERENCE]` 我就不能在下一段把它当事实引用。
② **把决策拆成「可逆」与「不可逆」**。架构上我尽量把不可逆的定下来、把可逆的留着：接口契约（`ModelResponse`、`Tool.permission`、`Actor`、审计列）是我愿意花时间定准的，因为改它代价大；具体实现（mock 的 prompt、chunk_size=1000、`OVER_FETCH=4`）我随手就能改。
③ **用约束代替预测**。我不猜「你们有多少用户」，我按 SPEC 与 JD 的硬约束做范围决策（本期禁止 K8s/微服务/任意 SQL/控制类动作），然后为「需求长出来时改哪一行」预留位置（`get_current_user` 是身份唯一入口、`queries.py` 是 SQL 唯一入口、`store.py` 是 Chroma 唯一入口）。
④ **给每个假设配一个证伪动作**。比如我假设「内网 + 私有推理是主形态」→ 那我的验证动作是入职第一周问清出域政策；我假设「328 行订单够演示」→ 验证动作是看有没有哪个 operation 在真实规模下会退化。
**这题我真正的回答是：我不知道的东西很多，但我有一套不让未知污染决策的记法。**」

#### My Project Evidence

- 本文件通篇的五类标签；`SPEC.md` §0.1 的「本期禁止」清单；三个「唯一入口」模块（`app/auth/dependencies.py`、`app/db/queries.py`、`app/rag/store.py`）

---

## Q25-04 讲一次你判断失误的经历。

#### 标准答案

「有一次很具体的：**我以为 Fix #5（审计内存有界化）已经解决了内存增长问题，其实我留了一条绕过它的旁路。**
- **我做了什么**：把 `AuditLog._records` 从 `list` 换成 `deque(maxlen=1000)`，配置化上限。这一步是对的。
- **我漏了什么**：`clear()` 里我写的是 `self._records = []` —— 一个**无界 list**。也就是说「重置」这个动作会把有界结构换成无界结构。它只在测试里被调用，所以没有任何测试会红，`ruff` 也不会管。
- **我怎么发现**：为写这份面试材料重读自己的 diff 时。
- **我当时为什么会犯**：Fix #5 的心智模型是「加个 maxlen」，我改的是**构造函数**那一处，没把「所有会给 `_records` 赋值的地方」当成一个集合去查。这是典型的**按症状修复而不是按不变量修复**。
- **正确修法（已落地）**：`self._records.clear()` —— deque 原地清空且保留 maxlen（比重新构造更简单也更不会错）。本轮一致性修复把它改了过来，并加了 `TestMemoryBound` 两条回归测试：清空后仍是 deque、maxlen 仍在、继续追加仍被截断、SQLite 里的行不受影响。
- **我从这件事抽出的规矩**：修一个约束时，先把「谁能让这个约束成立」全列出来（这里是所有赋值点），再动手；并且给这个约束配一条**旁路测试**（reset 之后再塞 5000 条，断言仍有界）。」

#### 加分动作

补一句：「同一批里我还发现了 `content: str` 被声明了两次（也是那次提交引入的）。所以我现在的规矩是：**审查提交本身也要被审一遍**。」

#### Pitfalls

- 不要挑一个「其实是优点的缺点」（「我太追求完美」）。挑一个有明确错误、明确发现路径、明确修正规矩的。
- 不要虚构造成生产事故的失误。

---

## Q25-05 你如何给非技术同事解释一个技术风险？

#### 标准答案

「我练过这个，对象是未来的业务部门（`[FACT]` JD 第 6 条要求培训支持内部业务部门）。我的结构是**三句话 + 一个选择**：
以「知识库没做文档级权限」为例：
① **现象用他们的语言**：「现在只要一个人能问，就能问到库里任何一份文档写的内容。」
② **后果挂到他们在意的事**：「不是黑客才会出问题——只要有人把一份只该给财务看的材料传上去，第二天一线同事问一个不相关的问题，它就可能出现在回答里，而且**带着看起来权威的引用**。」
③ **给出一个他们可以决策的选项**：「要么我们规定这个库里只放可以全员可见的材料（我来做入库审批），要么先花几天把权限做进检索里。**中间没有既省事又安全的选择。**」
**要点**：不说「metadata ACL 缺失」；不说「fail-open」；把技术词每次出现都换成「谁会因此看到什么」。并且**把决定权还给业务方**——平台工程师替业务方决定密级是最坏的做法，我的角色是让每个选项的代价可见。
我还准备了一个反面教训用在自己的代码上：「我不会告诉你『加了 AI 就能自动化』。我能告诉你的是它能查、能算、能写草稿，**以及它会在没有依据时拒答**——后者是设计目标不是故障。」这句我在面试里愿意对业务方说，也是我认为内部平台能不能被信任的关键。」

#### Follow-up Questions

- 业务方说「那我们要它全都答，别拒答」怎么回？（把风险写进使用规范 + 让他们的负责人签字确认哪些场景允许无引用回答；不是靠工程默认值硬扛）
- 他们听不懂怎么办？（用他们熟悉的一次具体事故倒推：「上周那份被废止的制度如果还在答案里，你能看出来吗？」）

#### Pitfalls

- 不要用类比炫技（「就像防火墙一样…」）；用**后果**说话。
- 不要暗示业务方「不懂技术所以没办法」——那是我在恒光这种组织里最不该有的姿态。

---

# 26 · 系统设计延伸题

### Q26-01 如果用户从 20 人变成 500 人，你的架构哪里先塌？

#### Short Answer

按塌的顺序：① 审计与业务同库同账号（合规先塌，不是性能先塌）；② 单进程内状态（`Metrics`/`AuditLog` 内存 + SQLite 写串行）让多副本不可行；③ 检索没有 ACL 与 rerank，语料一上量质量与越权同时暴露；④ 没有任何配额/超时，一个 Agent 循环能占住一条链路。

#### Standard Answer

`[MY DESIGN]` 我给「塌点 + 症状 + 替换方案 + 替换前置条件」四列：
| 顺序 | 塌在哪 | 症状（我怎么知道它塌了） | 替换 | 前置条件 |
|---|---|---|---|---|
| 1 | 审计的可信性 | 有人问「谁能改审计记录」我答不上来 | 审计独立库 + 只 INSERT 账号 + 链式锚定 | 不需要新硬件，**这是最容易做的**，也是我第一个要做的 |
| 2 | 单进程状态 | `--workers 4` 之后 `/metrics` 数字互相矛盾、`X-Request-ID` 无法跨进程串 | 指标与计数器进共享存储（Redis/Prometheus 拉模型），会话外置 | 需要一个 Redis 或 TSDB —— **这是它第一次真正必需**（见 §5 Q5-12） |
| 3 | SQLite 写 | 高峰期 `database is locked`、审计写入延迟 | Postgres（async driver；顺带解决我 async 路径里跑同步 DB 的缺陷） | 迁移脚本 + 恢复演练（没演练过的备份不算备份） |
| 4 | 检索层 | 空召回率升高 + 越权面随语料扩大 + 无 rerank 导致 top_k 被迫加大 | 真 embedding + rerank + 混合检索 + **metadata ACL**（先过滤后排序）+ 双索引别名 | **语料准入与 owner 流程**（没有它，检索做得越好错得越快） |
| 5 | 无预算/无限流 | 某些用户在长 Agent 循环上把 GPU/额度吃满 | 请求 deadline + 工具 timeout + 熔断 + 按用户滑窗限流 + 成本归因 | 先有 token/成本指标（今天只有 `usage` 透传） |
| 6 | 前端单页控制台 | 角色/部门差异需求进来（车间 vs 机关） | 拆成场景化入口 + 移动端；契约测试继续钉字段 | 需要真实用户反馈通道（点踩/纠错） |
**同时我会说一句最重要的判断**：500 人规模下**先崩的不是性能，是信任**——只要出现过一次「他问到了不该看到的东西」或者「答案看着对其实是从缓存里拿的别人的结果」，平台就没人用了。所以 1 和 4 排在 3 前面，这也是我为什么在 §11 的分阶段落地里把 ACL 放进第一期的原因。

#### Follow-up Questions

- 哪个塌点最便宜？（审计独立账号，几乎零代码改动）
- 你会先做水平扩容还是先补这些？（**先补 1/4**，因为水平扩容会把 2/3 变成事故；顺序不能反）

---

### Q26-02 设计一个多租户（多基地）的企业 AI 平台

#### Short Answer

三个隔离层次按需选择：共享应用 + 逻辑隔离（metadata/tenant 列）、独立 collection、独立实例。对恒光这种「三基地 + 子公司」结构我会用**应用共享 + 检索强隔离 + 审计按域分区**。

#### Standard Answer

`[MY DESIGN]` 我的设计（明确标注这是方案，`[PRODUCTION_NEXT]`）：
**① 租户模型**：`tenant`（法人/基地）+ `department` + `role` + `capability`（工具/operation）四维。判定 = 角色授权 × 数据范围，两者必须同时通过。
**② 隔离强度分级**（按数据敏感级别选，而不是全局选一档）：
- 低敏（制度、公开资料）：共享 collection + metadata 过滤（`tenant_id`, `allowed_roles`）；
- 中敏（本基地台账）：**独立 collection**（`hengguang_huaihua_v3`）+ 检索时按 principal 选集合，这样「选错集合」就是硬失败而不是过滤漏写；
- 高敏（研发配方、事故调查）：**独立索引 + 独立推理端点 + 禁止出域 + 答案不落审计正文**（只落事件）。
**③ 检索层是隔离的唯一强制点**：`retrieve(query, principal)`，内部**先按 principal 过滤再 top_k**（顺序反了会泄露排名与存在性，见 Q7-14）；集合选择也由服务端决定，模型与前端都没有「集合名」这个参数。
**④ 审计分区**：`audit_logs` 加 `tenant_id`；跨基地查询需要更高权限（`audit:read:cross_tenant`）——并且「跨域查审计」这条本身必须留痕。
**⑤ 缓存与配额**：任何缓存 key 都含 `tenant + principal + permission_version`（否则缓存就是越权通道，见 Q9-06）；配额与成本按 tenant 归因，这是基地负责人能不能被说服用平台的实际抓手。
**⑥ 身份**：接公司 SSO/LDAP，组织归属由身份系统给（我不在平台里维护人事数据），平台只维护「角色→能力」映射。
**⑦ 演进策略**：**第一天就把 `tenant_id` 放进 schema 与 metadata**，哪怕所有查询都恒等于单一租户。这一步是我在 Demo 里没做的（当前只有 role），也是我认为最典型的「晚做代价呈数量级上升」的字段。
**⑧ 明确不做**：不做跨基地模型权重差异（维护成本爆炸）；不做「每基地一套平台」（运维半径不允许，`[FACT]` 岗位招 1 人）；不做控制面（见 §13）。

#### Follow-up Questions

- 子公司与母公司数据能不能同库？（取决于法人数据治理，不是技术问题；我的架构对两种都能支持：同库靠 metadata，分开靠独立实例 + 统一网关出口）
- 谁来定密级？（数据 owner；平台只提供字段与强制点，**平台自己猜密级是最坏的设计**）

---

### Q26-03 设计一个知识库的权限系统

#### Short Answer

权限必须在检索层强制，并且是「身份 → 密级/范围 → 先过滤再排序 → 引用渲染再过一道 → 全程留痕」五段。任何一段都不能靠 prompt。

#### Standard Answer

五段展开（对应 `[PRODUCTION_NEXT]`，Demo 现状见 Q7-14 的承认）：
**① 身份段**：只来自请求（token/会话），绝不来自请求体里任何 `role`/`user_id` 字段（这是我在 Demo 里就守住的一条，见 Q17-04）。`Actor` 一路显式传递到最底层。
**② 授权来源段**：密级与范围**由文档 owner 在入库时声明**（`classification`、`tenant_id`、`allowed_departments`、`effective_from/to`），平台不猜。入库接口拒绝缺 owner 与缺密级的文档（**缺字段 = 拒绝入库，而不是默认公开**）。
**③ 检索段**：`store.query(..., where=ACL 谓词)` → **先过滤再 top_k** → 融合打分 → `min_score` 门槛。生产上还要保证「撤权后立刻生效」：ACL 变更触发受影响 `document_id` 的索引块重建（或至少让过滤谓词实时可读，不缓存权限）。
**④ 输出段**：答案与引用渲染再过一道（标题、摘要、URL 都可能敏感；「无权限」的措辞不能泄露文档存在性）；数字与事实的一致性校验也放在这里（引用一致性检查）。
**⑤ 追责段**：每次检索一行审计（含命中的 `document_id` 列表，不含 query 正文）；`denied` 与「命中被 ACL 清空」是两类不同事件（前者是越权尝试，后者是需求信号）；**读取审计本身要权限并留痕**。
**负例测试是这套系统的验收条件**：每条路径（API 检索、工具检索、Agent 引用渲染、缓存命中）都要有一个「低权限 + 敏感文档 → 断言不可见」的测试；并且要有一条「**把 ACL 字段拿掉时至少一条测试变红**」的元测试（我在 §12 里提过这个判据——能证明测试有效）。
**我明确反对的三个做法**：用 prompt 让模型「别提某些内容」；先 top_k 再过滤；把「文档不存在」和「你没权限」返回成同一个回答。

#### Follow-up Questions

- 怎么处理「一份文档多个密级段落」？（分块级 ACL：`classification` 落在 chunk metadata，入库时由 owner 或抽取辅助标注；这也是 heading 感知分块的额外好处——一个 chunk 不跨节，密级不必拆句）
- 时间维（制度废止）算权限吗？（算，`effective_to` 就是范围条件的一部分；废止制度被引用是安全事故，见 Q7-13）

---

### Q26-04 设计模型的私有化部署方案

#### Short Answer

先定任务再定硬件，而不是先买卡。我的最小方案：1 台单机多卡 + vLLM（或 Ollama 起步）跑一个对话模型 + 一个 embedding 服务 + 网关统一出口，配并发/长度双预算与降级策略；上线前必须有「在自己的评测集上」的质量与延迟基线。

#### Standard Answer

`[MY DESIGN]`（`[PRODUCTION_NEXT]`，明确标注我**没有** GPU 生产运维经验）
**第 0 步：先把需求量化，否则硬件决策就是赌博。**
要三个数字：① 峰值并发问答数（不是注册人数）；② 平均输入长度与 top_k 决定的上下文预算；③ 可接受的 P95 首 token 与完成时间。
`[INFERENCE]` 对恒光这种内部平台我会先假设「机关为主、峰值并发 ≤ 10、上下文 ≤ 16k」，然后**入职一周内用真实需求把这三个数字测出来替换掉我的假设**（并说明假设来源是我的判断，不是公司事实）。
**第 1 步：模型形态选择。**
- 对话模型：优先「OpenAI 兼容 + 支持 function calling」的开源模型（**Agent 全靠这条**，选型时我会把工具调用可靠性当作硬指标，见 Q6-09）；量化（AWQ/GPTQ/FP8）以换吞吐，代价是工具调用与数字精度可能先退化 → **量化版本必须在评测集上单独跑一遍**，这是我会坚持的一条。
- embedding：私有化跑一个中文 embedding 服务（OpenAI 兼容 `/embeddings`，我的 `OpenAICompatibleEmbeddingProvider` 直接可用）。
- 分类/抽取这类高频小任务：单独一个小模型（成本路由）。
**第 2 步：服务层。**
vLLM（吞吐/连续批处理/PagedAttention）而不是裸 HF transformers 起 API；`max_model_len` 与 `gpu_memory_utilization` 显式设，并且**在网关侧配一个小于服务侧超时的预算**（否则排队会让 60s 变成 600s）。Ollama 我用来做开发期便利（我的 provider 已支持它的 `/v1`），生产我不拿它当高并发服务层。
**第 3 步：容量与降级。**
两条预算线：**并发请求数**与 **token 长度**；超线不是崩，是排队 + 明确告知 + 可选降级到小模型（**降级必须显式，见 Q6-04/Q6-05**）。
关键设计：**知识问答可以「先给检索结果」再补答案**——这在模型满载时是体验最好的降级，因为它把平台的另一半价值（有据）保住了。
**第 4 步：出域政策（这一步不是技术，是制度）。**
云端 API 什么时候允许、允许传什么字段、谁批准——写进平台使用规范并落到网关的 provider 白名单里（**高密级域只能指向内网 base_url，这个约束我放在网关层，因为只有网关是单点出口——这就是「为什么要单独一层网关」在生产上最实在的答案**）。
**第 5 步：可观测与验收。**
必须有：每模型队列深度与 P95、显存与吞吐（tok/s）、失败率、token 成本按 tenant 归因、以及「评测集 + 量化版本 + 私有版本」三者对比表。验收判据我写三条：评测集上不显著劣于现有云端基线、峰值 P95 达标、以及**模型挂了的时候审计与鉴权照常工作**（这条我有信心，因为今天就是这样）。
**我承认的边界**：`[需要本人确认：是否有真实 GPU 部署/vLLM 运维经历]` 如果没有，我会说：「这是我把原理与判据说清楚的程度，实际显存与并发调优我要在你们的硬件上做一轮才敢说。」

#### Follow-up Questions

- 一张消费级卡能干什么？（小模型 + 低并发 + 开发验证；我不会拿它当生产答复）
- 要不要上多机推理？（在内部平台规模下，我先把「队列 + 预算 + 降级」做好；多机张量并行通常是买错方案的开始）
- embedding 与 chat 不同机器部署，一致性怎么保证？（版本三元组进审计：embedding 模型版本 + 索引版本 + 对话模型版本，见 Q15-06）

---

### Q26-05 设计一个 Agent 的记忆系统

#### Short Answer

分四类记忆（工作/会话/情节/语义），各自有明确的写入者、TTL、权限与可追责要求。**当前 Demo 一个都没有**（messages 每次从 `[policy, user]` 重建），所以这是设计题不是经验题。

#### Standard Answer

`[MY DESIGN]` `[PRODUCTION_NEXT]` 我的方案：
| 类型 | 内容 | 写入者 | 检索方式 | TTL | 权限要求 |
|---|---|---|---|---|---|
| 工作记忆 | 本次 loop 的 messages/tool 结果 | runtime | 就地累积（现有实现） | 一次运行 | 无（进程内） |
| 会话记忆 | 多轮上下文 + 已确认的澄清 | 会话服务 | 直接加载 + 压缩 | 会话周期 | 会话属主（`session_owner` 必须进查询条件） |
| 情节记忆 | 「这个用户上次问过 X，答案是 Y（带引用）」 | 答案落库时 | 向量 + 时间衰减 | 可配（默认 90 天） | **必须带 principal/tenant 谓词**，否则一个人的偏好会出现在另一个人的答案里 |
| 语义记忆 | 沉淀的事实/术语/常用口径 | **人工或审批后** | 结构化表 | 长期，版本化 | 与知识库同一套 ACL（**它就是知识库的一部分**） |
四条我认为决定成败的规则：
① **记忆的写入要过和检索一样的权限判定**，而不是「先进去再说」。会话内容里可能含敏感原文，落库那一刻就是数据分级事件。
② **可追责优先于连续性**：每条记忆带来源（哪次运行、哪个 request_id、引用了哪些 `document_id`）。当记忆和知识库冲突时，**知识库版本优先**，并把冲突记成一条运营事件（这意味着用户被一个过期记忆回答了）。
③ **记忆必须是可撤回的**：用户能问「你记得我什么」并删掉；管理员撤权时必须连带清掉相关情节记忆。**能写入但删不掉的记忆，是合规负债**。
④ **不要一上来做「长期人格化」**。企业内部平台的收益来自「少问一次、口径一致」，不来自「它了解我」。我会先做会话记忆（ROI 最高、风险最低），再评估情节记忆，语义记忆走知识治理流程而不是自动沉淀。
**我会主动说的反面判断**：多 Agent + 共享长期记忆这个组合，在权限与审计上的复杂度是乘法而不是加法。这也是我在 §11 里把它放到第四期之后的原因。

#### Follow-up Questions

- 上下文压缩放哪层？（会话服务，不在网关也不在 Agent loop；压缩要保留引用编号，否则我的 `[n]` 契约就断了——这是个具体的坑）
- 记忆要不要进向量库？（会话不需要；情节需要，但它的索引必须与知识库**物理分开**，因为检索时它是「个人历史」而不是「权威依据」，混在一起模型会拿个人历史当依据回答业务事实）

#### Pitfalls

- 不要说「我的 Agent 有记忆」。它没有。
- 不要把「记忆」和 RAG 混为一谈（一个是个人历史，一个是权威知识，二者对答案的**证据等级**不同）。
# 29 · 性能、成本与运维监控（JD 第 4、5 条）

> `[FACT]` JD 第 4 条要求「平台日常运维、监控、性能优化与故障处理」，第 5 条要求「大模型接入、评测与切换，结合成本和效果优化选型」。
> 本节先说清前提：**我没有生产负载可优化**。我能给的是「我现在测到了什么、我测不到什么、上线第一周我会怎么补」。

## Q29-01 性能怎么样？瓶颈在哪？

#### Short Answer

演示负载下延迟由两件事决定：mock 路径几乎全在检索与 IO（毫秒级），真实 provider 路径几乎全在模型网络往返（秒级）。所以现在唯一的瓶颈是模型调用；等语料和并发上来，瓶颈会依次变成 embedding 计算与向量检索、SQLite 写、最后才是 Python。

#### Standard Answer

`[MY DESIGN]` 已实测（可指证据）：423 个测试全跑 **约 15 秒**（23 个文件、含 6 篇文档的临时 Chroma 与 mock embedding）；`/health`、`/metrics`、`/api/knowledge/documents` 都在毫秒级（测试里用 `TestClient` 直接断言，没有慢用例）；Docker 的 `start_period: 40s` 是因为 Chroma 首次加载需要时间（这是我在部署阶段实测出来的）。
`[INFERENCE]` 结构性判断（我会这样标注）：
1. **模型调用占绝对主导**：RAG 一次问答 = 1 次 embedding + 1 次向量查询 + 1 次 chat；Agent 一次运行 = `steps` 次 chat + 工具查询。provider 超时 `60.0` 秒，意味着一次 Agent 运行最坏可占用分钟级；而 `max_steps=5` 把上界钉成了「5 次模型调用 + 8 次工具调用」——**这是性能上限的设计定义，不是估算**。
2. **本地 mock 路径「很快」不能外推到真实 provider**，这条我要主动说。
3. **语料规模 45 个 chunk**：`MAX_CANDIDATES=200` 的过取逻辑在 `top_k=5` 时取 20 条候选。换成 4.5 万个 chunk 时，Chroma 的 ANN 与我的融合重排（Python 里做）都会变成成本项——**重排是我实现里最先需要下沉/并行的那一段**。
4. **写路径的瓶颈在 SQLite**：每个动作至少一行审计。并发一高 `database is locked` 会先出现（单写者），所以我把它列为迁移 Postgres 的首要触发条件（§20 Q20-02）。
**我必须承认没有的观测手段**：没有分位数（只有均值 + 峰值）、没有 per-query 计时、没有火焰图/pprof、没有并发压测、没有 GPU/显存指标（我没有跑私有推理）。
`[PRODUCTION_NEXT]` 上线第一周的性能动作：① `/metrics` 加 histogram（P50/P95/P99，按端点与按模型）；② `observe_usage`（token 与估算成本，按 tenant）；③ 给每个 operation 建立 SQL 延迟基线（慢的一律加索引或改预聚合）；④ 用 `k6`/`locust` 打一轮阶梯负载，找出**第一个真正塌的组件**（我预判是模型端点排队，其次是 SQLite 写）；⑤ 压测顺便验证预算不等式（工具 timeout 之和 ≤ Agent 墙钟 ≤ HTTP 超时）在负载下成立。

#### Follow-up Questions

- 怎么在不影响用户的情况下优化检索？（双索引灰度 + 影子对比；改 `top_k`/`min_score` 走评测集回归，不走线上 A/B——因为「看起来快」不是判据）
- 要不要缓存？（分两类：**LLM 响应缓存我默认不做**，答案带权限语义、且缓存命中会绕过 ACL；**检索结果缓存**放服务端，key 含 `principal + permission_version + 语料版本`，TTL 短，撤权即失效。）
- 首 token 延迟重要吗？（对内部问答体验最重要，所以我需要流式输出——而我今天是 `stream=False`，这是明确缺口。）

#### Pitfalls

不报任何编造的 QPS 或延迟数字；不把「测试跑得快」当性能证据（它证明的是回归成本，不是吞吐）。

#### Interview Keywords

`latency is model-dominated` `max_steps is a latency bound by design` `no percentiles yet` `cache must key on principal or not at all`

---

## Q29-02 成本怎么控制？

#### Short Answer

成本 = 单价 × 用量 × 调用次数。三者都可控：调用次数靠预算与工具裁剪，用量靠上下文收缩（top_k、双视图、压缩），单价靠任务路由与私有推理。前提是**先有归因**——而归因我今天缺一半。

#### Standard Answer

`[MY DESIGN]` 现状：`ModelResponse.usage` 已把 provider 返回的用量透传出来，`latency_ms` 也有，端点级平均延迟也有；**但没有 token/成本计数、没有按部门或按 agent 的归因**。所以我今天只能说「有原料」，不能说「有成本控制」——这句话我会先说。
`[PRODUCTION_NEXT]` 成本控制顺序（按 ROI）：
① **归因先行**（1 周）：`observe_usage(tenant, endpoint, model, prompt_tokens, completion_tokens, cost_est)` + 一张日报看板。没有归因的成本优化最后一定变成「让大家少用 AI」。
② **砍调用次数**：`max_steps`/`max_tool_calls` 是成本阀不只是保险丝；按角色裁剪可见工具集（`allowed_tool_names` 接到 loop）既降错选率又降 prompt 体积。
③ **砍用量**：我的「双视图输出」（模型看 8 行文本、完整 payload 给平台）就是这个方向最典型的实现——**让模型读摘要而不是读表**；再加上下文压缩与相邻 chunk 去重。
④ **砍单价**：任务路由——分类/抽取/格式化走低价或私有小模型，复杂多步分析走强模型；路由决策落在网关并写进审计（**降级/换模型必须显式**，§6 Q6-04）。
⑤ **结构性方案**：私有推理把边际成本变成算力成本，优化目标随之从「少花 API 费」变成「提高每张卡的吞吐」（连续批处理、量化、更长上下文复用）——**这是完全不同的优化题**。
⑥ **配额与治理**：按部门/用户配额 + 软阈值提醒 + 硬阈值限流（429 错误码已预留但无生产者，§16）；成本数据回流到「哪个场景值得继续做」的产品决策——`[FACT]` 这正是 JD 第 5 条「结合成本和效果优化选型」的落地形态。
`[INFERENCE]` 一个我会主动提的判断：**内部平台最常见的浪费是「把每个问题都当成需要强模型的问题」**，其次是「为了显得准而把 top_k 开大」。这两个都是平台层可治理的，不需要业务方配合——这也是平台工程师在成本上真正的价值点。

#### Follow-up Questions

- 怎么估一个问题的成本？（tokens ≈ 系统 prompt + 工具 schema + top_k × chunk 大小 + 历史；单价 × (prompt+completion) × 调用次数。我可以现在用我的阈值算一个上界：5 步 × (约 5×1000 字中文上下文 + schema)。）
- 缓存能省多少？（我给不出百分比，命中率的决定因素是「问题是否重复」，内部知识问答的重复率我没数据。**先量再谈省**。）

#### Pitfalls

不报任何单价或折扣数字（价格随时间与渠道变化）；不把「便宜模型」当默认答案——换便宜模型之前必须过自己的评测集，否则省的可能是钱、赔的是信任。

#### Interview Keywords

`attribution before optimization` `dual-view output is a cost decision` `budget is a cost valve` `route by task with explicit degraded`

---

## Q29-03 监控告警怎么设计？

#### Short Answer

三层：可用性（健康探针 + 错误码分布）、性能（P95 + 队列与超时）、质量（拒答率、空召回率、引用一致性、反馈率）。**只有第一层我今天有一半（指标端点有、告警规则没有），后两层完全没有。**

#### Standard Answer

`[MY DESIGN]` 我今天能拿出的只有「数据面」：`/health`（进程 + 数据库探针 + `seeded` 布尔）、`/metrics` 的 15 项计数器（`error_by_code`、`requests_by_endpoint`、`permission_denied_count`、`agent_runs_by_status`、`audit_write_count`…）、`audit_logs` 全链可查、结构化 JSON 日志带 `event` 名。**没有告警规则、没有 dashboard、没有 SLO**——这两者的区别我面试里不会混。
`[PRODUCTION_NEXT]` 三层告警（每条都写清**阈值来源**）：
**① 可用性（分钟级响应）**：`/health` 连续失败；5xx 比例超阈值；`error_by_code` 里 `PROVIDER_ERROR`/`DATABASE_ERROR`/`STORAGE_ERROR` 突增；**审计写失败计数 > 0**（这条最容易被漏也最不该漏：一个不记录的平台在企业里是不合格的工具）；容器重启；磁盘（`data/runtime` 与 Chroma 会涨）；连接池耗尽。
**② 性能**：端点 P95 超 SLO；Agent `max_steps`/`max_tool_calls` 触发率突增（**这是模型行为退化的信号，不只是容量信号**）；provider 延迟分位漂移（供应商侧劣化的最早征兆）；队列深度（如引入异步）。
**③ 质量（内部平台的真正生死线）**：拒答率与空召回 top query（涨 = 知识库缺料或权限过滤过紧）；引用一致性失败率；用户「有误」反馈率；`degraded` 比例；按 tenant 的成本突增。
**两条纪律**：① 每条告警必须对应**一个人的一个动作**（否则是噪音，我会写清 owner）；② 阈值来自基线而不是抄文档——上线第一周只做「记录基线 + 不发通知」，第二周才设阈值。**「先静默观测两周」是我认为最省双方时间的做法**。
**值班与故障处理**（`[FACT]` JD 第 4 条含「故障处理」）：`request_id` 是唯一入口。SOP 我会写成：拿 request_id → `/api/audit/{id}` 定位环节（鉴权/网关/工具/DB）→ 看 `/metrics` 判断是全局还是单点 → 按「降级开关」（`LLM_FALLBACK`、摘工具、只读模式）止血 → 事后把这次故障沉淀成一条测试或一条评测样本。**最后一步是让系统变好的唯一部分，我会坚持它。**（展开版见 Q29-04。）

#### Follow-up Questions

- Prometheus 还是自研？（`snapshot()` 是单一日出点，加 exposition 序列化即可接上；标准方案 + 外部 TSDB，告警生态不在我手上重造的价值）
- SLO 定多少？（我不知道你们的用户期待。我的答案是「用两周基线定，不现在给你一个数」——比编一个「99.9%」负责。）

#### Pitfalls

不说「我们有监控告警」——我有的是**指标端点**，两者不是一个东西；不提没设过的 SLA 数字。

#### Interview Keywords

`three alert layers` `audit write failure must alert` `budget exhaustion is a model-quality signal` `baseline before thresholds`

---

## Q29-04 线上突然全部 502，你怎么办？

#### Short Answer

先分诊再动手：是「模型侧」还是「平台侧」。第一步不看代码，看 `/metrics` 与一条 `request_id` 的审计链；第二步止血（摘能力/只读模式/显式降级）；第三步修；第四步把这次故障变成一条测试。

#### Standard Answer

`[MY DESIGN]` 动作序列（以我这套代码的实际控制面为准）：
**T+0 分诊（分钟级）**
```bash
curl -s :8000/metrics | jq '.error_by_code, .requests_by_endpoint'
curl -s :8000/health | jq .
curl -s -H "Authorization: Bearer <admin>" ":8000/api/audit?status=error"
```
判据：`PROVIDER_ERROR` 占绝对多数 → 模型侧；`DATABASE_ERROR`/`STORAGE_ERROR` → 存储侧；都不是但 `agent.run=error` + `INTERNAL_ERROR` → 代码侧；`/health.database.initialized=false` → 启动/挂载问题（我部署时踩过：SQLite 路径相对 CWD 解析错，数据库在另一台容器里打开成了空库）。
**T+5 止血**
- 模型侧：先直连端点确认是端点故障还是网络/配额。此时**开 `LLM_FALLBACK` 之前先想清代价**：它给的是「格式正常的无意义答案」，所以它属于**需要决策者知情才能启用的降级**——我会明报「现在可选 A 报错 / B 降级并告知用户」，而不是自己按开关。这是对 §6 Q6-04 的兑现。
- 更好的止血是**摘能力**：把受影响 provider 从注册里去掉（或 `LLM_PROVIDER=mock` 只保检索与工具），因为平台核心价值之一是「有据的检索」，它不依赖生成也能给引用清单。
- 存储侧：SQLite 锁 → 停写路径（关 ingest、暂停可写操作），或按预案恢复备份。
**T+30 修复与验证**：定位到具体异常类型（日志 `error_type` + request_id），修，**跑全量 423 测试**，再灰度恢复。
**T+1 天 复盘产出**：① 这次故障有没有一条测试能提前抓住？没有就写；② 有没有指标能提前 10 分钟报警？没有就补（如 `audit_write_failure_count`）；③ 用户侧可见性够不够（「502 时前端显示了什么」最常在复盘时被想起）；④ 是否要在 §11 的阶段计划里调优先级（例如「多 provider + 熔断」被这次故障证明了优先级）。
**我不做的三件**：不重启了之（它掩盖 provider 抖动与内存问题的区别）；不在没有 request_id 证据时改代码；不把「开了 fallback」当修复。

#### Follow-up Questions

- 用户投诉「答案不对」（不是 502）？（那是质量事故不是可用性事故：拉 request_id → 看 `model`/`provider`/`degraded` → 看 `sources` → 判定是检索缺失、引用错配、还是模型不守策略；三者三种修法，**不能一律「加 prompt」**。）
- 怎么知道有没有真实影响到用户？（`/api/audit` 的 error 行数 × 涉及用户数，比 5xx 计数更接近「谁被影响了」。）

#### Pitfalls

不说「我们会自动切换备用模型」并把它当优点（静默切换在我这里是缺陷，§6 Q6-05）；不跳过分诊直接给修复方案。

#### Interview Keywords

`triage by error_by_code` `stop the bleeding by removing capability` `fallback is a decision not a default` `every incident ends in a test`
# 27 · 项目证据速查表

> 用途：面试现场被问「你确定？」时，**30 秒内报出可验证的数字与文件**。
> **代码证据基线：`460a6ee`**（Day 1–5 + Audit Fix；实测时间 2026-10-01）。本轮最终一致性修复只动了文档、两处代码缺陷与新增测试，下表已按**当前工作树**复核。

## 27.1 数字卡（背这半页就够）

| 维度 | 数字 | 我怎么验证 / 在哪 |
|---|---|---|
| 测试总数 | **423 passed**（单元 291 + 集成 132），23 个测试文件 | `uv run pytest -q` → `423 passed, 2 warnings in ~15s`；`--collect-only -q` 分文件计数 |
| 测试增长轨迹 | Day1–3 `139` → Day4 `380` → Day5 `410` → 代码基线 `460a6ee` 时 `420` → 后续 `422` → 当前 `423` | `README.md` 测试基线行（**已与实测一致**）+ `--collect-only -q` |
| Python 代码量 | `app/` 63 个 .py 文件，**7649 行** | `find app -name '*.py' \| xargs wc -l` |
| 测试代码量 | 24 个 .py，**4639 行** | 同法 |
| 前端代码量 | `web/src` 17 个 .ts/.tsx，**3133 行**（5 个页面，无 UI 框架） | `find web/src -name '*.ts*' \| xargs wc -l` |
| 文档量 | 4 份 2165 行（`SPEC 1714` / `README 246` / `ARCHITECTURE 133` / `DEMO_SCRIPT 72`） | `wc -l` |
| 提交历史 | 代码证据基线 `460a6ee` 时 **7 个提交**（Day1 → Audit Fix）；含面试材料与一致性修复后为 **9 个提交** | `git log --oneline` |
| HTTP 端点 | **11 个**：`/health` `/metrics` `/api/chat` `/api/agent/run` `/api/knowledge/{ingest,documents,search}` `/api/models` `/api/audit` `/api/audit/{request_id}` `/api/users` | `grep -r "@router" app/api` |
| 角色 / 权限 | 3 角色 / **10 权限**（7 路由族 + 3 工具族） | `app/auth/permissions.py::Permission` |
| 工具 | **4 个只读工具**，operation 白名单共 **7（ERP）+ 5（Safety）= 12** | `app/agent/tools/`、`build_default_registry` |
| 知识库语料 | **6 篇公开文档 / 45 个 chunk** | 实测脚本（临时 Chroma + mock embedding）→ `docs: 6 chunks: 45 skipped: [] errors: []` |
| 合成业务数据 | 9 张表：3 用户 / 8 供应商 / 10 物料 / ~328 采购订单 / 9 库存 / 6 设备 / 6 维修记录 + 安全事件 | `data/synthetic/seed.json`、`app/db/models.py` |
| 运行依赖 | **8 个**（fastapi, uvicorn, pydantic, httpx, sqlalchemy, chromadb, pyyaml, pypdf）+ dev 3（pytest, pytest-asyncio, ruff）；**无 LLM 框架** | `pyproject.toml` |
| 静态检查 | `ruff check .` PASS；`ruff format --check .` **PASS**（101 个文件全部已格式化） | 实测 |
| 前端构建 | `tsc -b && vite build` PASS（README 记录） | `README.md:22` |
| 关键阈值 | chunk 1000/overlap 150/top_k 5/min_score 0.10/embedding 1024 维/max_steps 5（上限 20）/max_tool_calls 8（端点 top_k ≤20、limit ≤50、days ≤365、tool rows ≤50、message ≤8000、query ≤2000、审计摘要 ≤12 keys / ≤160 字符 / 内存 1000 条） | `app/config.py`、`.env.example`、各 args_model |

## 27.2 「一句话定位」索引（被问到某模块时直接跳）

| 你被问到 | 一句话 + 一个文件 |
|---|---|
| 网关 | 一个 `chat()`、两类 provider、三件决策（注册/路由/降级），降级要打标 —— `app/gateway/router.py` |
| RAG | 标题感知分块 + 融合打分 + 引用契约 + 无依据拒答 —— `app/rag/{chunker,retriever,prompt}.py` |
| Agent | 60 行有限 loop，三个出口保证终止 —— `app/agent/runtime.py` |
| 工具 | 白名单 → 权限 → 校验 → 执行，失败是数据不是异常 —— `app/agent/executor.py` |
| 权限 | 两族互不继承，路由 + 工具各查一次，全部 fail-closed —— `app/auth/permissions.py` |
| 审计 | 一行一动作，集中净化，被拒也记，写失败不打挂请求 —— `app/observability/audit.py` |
| 关联 | 一个 `req_<uuid4>` 从 HTTP 追到工具 —— `app/observability/middleware.py` |
| 错误 | 一个信封：`detail` 给人、`error.code` 给程序，绝不回 traceback —— `app/api/errors.py` |
| 数据 | 合成库 + 固定 operation + 参数绑定，模型碰不到 SQL —— `app/db/queries.py` |
| 部署 | 两个容器 + `:ro` 语料 + healthcheck 门控启动 + 变量 upstream —— `docker-compose.yml`、`web/nginx.conf` |
| 前端 | 5 个页面全走真 API，字段由 30 个契约测试钉住 —— `web/src/`、`tests/integration/test_web_console_contract.py` |
| 自审 | 10 项检查 9 项落地，且发现「修复自己引入的缺陷」—— `git show 460a6ee` + §21/§22 |

## 27.3 我可以现场做的四件事（提前确认环境能跑）

1. `uv run pytest -q` → 约 15 秒 423 绿（**证明「423」不是嘴说的**）；
2. `docker compose up --build` → 打开 `:3000` 跑 `DEMO_SCRIPT.md` 六步（约 5 分钟）；
3. 演示越权：Dashboard 切到 operator → Agent 问采购金额 → 时间线里出现 `PERMISSION_DENIED` 但页面不崩（`DEMO_SCRIPT.md` Step 5）；
4. 演示追溯：拿 Step 3 的 `request_id` 打开 Audit 面板，一条链看到 `agent.run` + `tool.call` + `chat.complete`（Step 6/7）。
`[需要本人确认：面试形式是否允许现场演示；若为线上，准备录屏作为后备]`

#### Pitfalls

- 报数字前先说**量级与条件**（「6 篇公开文档 45 个 chunk」要紧跟「语料只有这个规模，所以检索质量不能外推」）。
- 不要把「423 个测试」说成「测试覆盖率 100%」——我**没有**测覆盖率数字（无 `--cov` 配置）。准确表述：「423 个断言覆盖的行为路径，未测覆盖率」。

---

# 28 · 开源组件评估（JD 第 2 条对照）

> `[FACT]` JD 第 2 条要求「持续研究开源 LLM 应用生态（Dify、RAGFlow、FastGPT、One-API/New-API、MCP 协议等）并评估引入」。
> **本节所有关于外部产品能力的事实性描述都标 `[INFERENCE]` 或待核实**：我读的是它们的公开文档，**我没有把它们跑进生产**。这是本节唯一允许的立场。
> `[需要本人确认：面试前是否要针对当前版本重新核对某产品的公开能力矩阵]`

## Q28-01 我怎么评估一个开源 AI 组件要不要引入？

#### Short Answer

八个维度的固定问卷：它替代掉我哪一段代码 / 它的边界能不能被审计 / 权限与数据流向 / 部署与运维半径 / 升级与锁定风险 / 性能与成本 / 生态与维护信号 / 退出成本。**结论必须写成一页纸并给判据，不能写「好用」。**

#### Standard Answer

`[MY DESIGN]` 我的问卷（这也是我打算入职后写技术评审文档的模板）：

| 维度 | 我要回答的具体问题 | 淘汰信号 |
|---|---|---|
| **替代范围** | 它删掉我哪一段代码？那段代码我今天怎么坏的？ | 说不出「删什么」= 只是在加一个依赖 |
| **可审计边界** | 检索排序、权限判定、prompt 组装这三件事**谁决定**？我能不能看到并改？ | 关键决策在黑盒里且不可插 → 企业平台上不了 |
| **数据流** | 它会往哪里发数据（含遥测）？会不会落业务数据副本？日志里有正文吗？ | 说不清数据流 = 不能碰内部数据 |
| **身份与 ACL** | 能不能接进我们的身份体系？文档级权限在哪层强制？ | 只能「全库可见」→ 与 §26 Q26-03 冲突，直接淘汰于第一期 |
| **运维半径** | 几个进程、什么中间件、几块卡、谁备份？`[FACT]` 岗位 1 人 → 这是硬约束 | 需要专职 SRE 才养得活 → 本期不引入 |
| **升级与锁定** | 版本节奏、破坏性变更历史、私有 DSL 依赖、能不能导出 | 用它的工作流 DSL 定义业务 = 迁移成本不可控 |
| **性能与成本** | 同一评测集上的 P95、token 成本、显存与吞吐 | 没有我自己的评测集 → **评估不成立**（所以我第一优先做评测集，见 §11 第一阶段） |
| **维护信号** | issue 响应、release 频率、贡献者集中度、许可证、是否有商业主体 | 单人仓库 + 高活跃度 = 停更风险要写进结论 |
**最后一格是我问卷的固定收口：「退出成本」**——如果两年后要拿掉它，我要改几处？我的判断标准：**退出成本低到我能承诺，才允许它在核心链路上。** 这也是我今天为什么把网关、检索、执行器都做成薄层：任何一块被换成外部组件，`app/api/` 与审计契约都不动。

#### Follow-up Questions

- 你怎么防止评估变成「选个最流行的」？（同一评测集 + 同一场景清单打分，分数写进文档；流行度只作为「维护信号」里的一格）
- 谁来批？（技术评审我写、数据与安全侧签；`[FACT]` 这正是 JD 第 6 条「沉淀平台使用规范」的落点）

#### Pitfalls

- 不要在面试里报任何我没验证过的具体功能清单（版本号、是否支持 rerank、是否支持 OIDC 都可能已经变了）。说法应是「按公开文档它定位是 X，**具体能力我要在当前版本上验**」。
- 不要说「开源的都太浅/不可控」这类一刀切。

#### Interview Keywords

`8-dimension questionnaire` `what code does it delete` `exit cost is the gate` `eval set first`

---

## Q28-02 Dify / RAGFlow / FastGPT / One-API / MCP 分别是什么定位？

#### Short Answer

四类东西：应用编排平台（Dify、FastGPT）、以检索质量为核心的 RAG 引擎（RAGFlow）、模型网关服务（One-API/New-API）、协议标准（MCP）。**它们不在同一层，所以「选哪个」通常是个错问题；正确问题是「哪一层需要它」。**

#### Standard Answer

`[INFERENCE]` 以下定位来自公开文档阅读，**不是生产使用经验**（面试我会先声明这句）：
| 组件 | 我的定位判断 | 在我的架构里它替代什么 | 我不用它的原因（本期） | 我什么时候会认真引入 |
|---|---|---|---|---|
| **Dify** | LLM 应用编排平台：可视化工作流、应用发布、知识库管理 | 整个「能力层 + 一部分前端」，包括我的 loop 与工具编排 | 它会把权限判定、检索排序、prompt 组装变成它的决定；企业 ACL 与审计我要能审计 | 需要让业务部门**自己**搭应用、并且它的权限模型能接进 SSO 之后 |
| **FastGPT** | 同类：知识库问答 + 流程编排 | 同上（更偏知识库问答一体化） | 同上；且我练的是平台层判断，不是配置流程 | 场景是「文档问答类需求大量重复」且我要快交付时 |
| **RAGFlow** | 以**深度文档理解与检索质量**为核心的 RAG 引擎（其公开定位强调解析/分块/引用这类检索侧功夫） | **我的 `app/rag/` 那一整块** | 它的检索我拿不到评测集对比，而本期我要先证明管线成立 | 我的评测集显示 recall@k 与表格解析质量是瓶颈时（**这几乎一定会发生**，因为我的 chunker 不处理表格，见 Q7-03）→ 那时我可能保留网关/Agent 层而**只换检索** |
| **One-API / New-API** | 模型网关**服务**：多渠道、令牌、计费/配额、故障转移 | 我的 `app/gateway/` 的 provider 注册与出口部分（不是它的语义契约） | 一个额外进程 + 额外运维面，本期不需要 | 出现多部门配额、成本归因、多渠道故障转移需求时；届时我把 `OpenAICompatibleProvider.base_url` 指过去，**`degraded/usage/citation` 契约留在自己这层**（Q23-06） |
| **MCP** | 协议，不是产品：标准化「工具/资源/提示」的跨进程提供方式 | 我的 `ToolRegistry` + `openai_schemas()` 的对外表达 | 只有 1 个宿主 + 4 个同进程工具，收益不成立（Q10-05） | ≥2 个 AI 宿主且 ≥3 个能力提供方（尤其 ERP/OA 团队自己发布 server 时），见 Q10-06 |
**这张表我真正想传达的结论**（面试收尾用）：
「我评的不是『谁更强』，是**它落在哪一层**。我的 Demo 里所有替换决策都已经被抽象挡住了：换检索引擎改 `app/rag/`、换网关服务改 `app/gateway/openai_compatible.py` 的 base_url、接 MCP 加一个 `Tool` 实现类，**而 `app/api/`、审计契约、权限矩阵三处不用动**。如果我连这三处的不变性都拿不到，那我引任何组件都是在给自己埋第二次重写的雷。」

#### Follow-up Questions

- 那你会不会第一天就全用现成的？（不会。我第一周要做的是**自有评测集 + 出域政策 + 身份接入**这三件，它们不属于任何开源组件，却决定后面所有选型能不能落地）
- 如果公司已上了 Dify？（那我退到平台层：网关统一出口、ACL、审计外送、评测与成本，并把 Dify 当消费方；见 Q23-04 的加分动作）

#### Pitfalls

- **绝对不要**说「Dify 不支持 X」「RAGFlow 的 rerank 比 Y 好」这类具体能力断言，除非我当场能引用当前文档。说「它的公开定位是 X，具体能力我要在当前版本验」。
- 不要把五者并列成「五选一」。层次不同是这题的正确答案核心。
- 不要说这些产品的 star 数、价格、融资情况（我没验证过）。

#### Interview Keywords

`layered positioning not product ranking` `eval set is the prerequisite` `abstraction protects the swap`
# 30 · 技术文档、使用规范与内部培训（JD 第 6 条）

## Q30-01 你怎么写技术文档？

#### Short Answer

按「读者要完成的动作」组织，不按「模块清单」组织。我这个仓库里有四类文档，各服务一种动作：能跑起来（README）、为什么这样设计（ARCHITECTURE）、照着做一遍（DEMO_SCRIPT）、当初要求是什么（SPEC）。

#### Standard Answer

`[MY DESIGN]` 四份文档各自的定位（我可以逐份说清它存在的理由）：
| 文件 | 服务的动作 | 我刻意做的取舍 |
|---|---|---|
| `README.md`（238 行） | 「十分钟内跑起来并看到效果」 | 顶部先放**免责声明 + 一览表 + 6 张截图**，再放快速开始；curl 示例直接可复制（token 是公开的演示凭据，这是为演示刻意设计） |
| `ARCHITECTURE.md`（133 行） | 「改代码之前先读这个」 | 只写边界与调用链，不重复 README 的命令；明确「谁能调谁」 |
| `DEMO_SCRIPT.md`（72 行） | 「照着点一遍就能演示」 | 六步、每步一句话 + 预期看到的字段；专门有一步演示**权限被拒但不崩**（因为这才是平台的卖点） |
| `SPEC.md`（1714 行） | 「当初的约束是什么、范围到哪」 | 有 §0.1「本期禁止清单」（K8s/微服务/任意 SQL/控制类动作等）——**这一节是我 5 天不失控的原因**，也是面试里我能回答「为什么不做 X」的依据 |
我的三条文档纪律：
① **写「为什么不」比写「是什么」值钱**：SPEC 的禁止清单、README 的 §已知限制、代码里 `AuditLog.record` 注释解释「为什么匿名事件不落库」，这三处是我最想让面试官看的；
② **文档必须可验证**：每条命令我都跑过，每个数字我都收集过（并且因此发现 README 的数字已经过时 —— 见 §34）；
③ **文档和代码一起改**：Fix 提交里同时改了 4 份文档（`git show 460a6ee --stat` 可查），否则文档在第二周就变成谎言集合。

#### My Project Evidence

- `README.md`、`ARCHITECTURE.md`、`DEMO_SCRIPT.md`、`SPEC.md`（合计 2165 行）
- `README.md` §已知限制、`data/synthetic/README.md`（合成数据声明 + 文件说明）、`data/documents/README.md`（语料准入说明）
- 6 张真实截图（`screenshots/`：dashboard / agent-rag / agent-erp / permission-denied / audit-trace / knowledge）

#### Follow-up Questions

- 文档过时你怎么发现？（`[PRODUCTION_NEXT]` 用测试钉文档：断言 README 声明的测试数 == `pytest --collect-only` 的收集数；断言 README 里出现的文件路径都存在。**「文档断言测试」是我打算加的第一条，因为 §34 里那三条漂移全是这一类**）
- 你会写 ADR（架构决策记录）吗？（会，而且我的 SPEC §0.1 + 这份面试材料的 §5/§23 事实上就是 ADR 的形态：决策、判据、代价三段。`[PRODUCTION_NEXT]` 正式引入 `docs/adr/NNNN-*.md`，每条一页，评审后不可静默修改）

#### Pitfalls

- 不要说「我文档能力强」——给出四种读者动作 + 对应四份文件，比形容词有力。
- 不要漏了「文档漂移」这个反面事实：我自己的 README 就有 3 处漂移（§34），**先自曝比被发现强**。

#### Interview Keywords

`docs organized by reader action` `write the "why not"` `docs verified by tests` `ADR shape already present`

---

## Q30-02 你会怎么给业务部门做 AI 平台培训？

#### Short Answer

培训的目标不是「教会用」，是「**让人知道什么时候不能信**」。所以第一课的内容是拒答、引用与责任链，而不是按钮在哪。

#### Standard Answer

`[MY DESIGN]` `[PRODUCTION_NEXT]`（对应 `[FACT]` JD 第 6 条「培训支持内部业务部门使用 AI 平台 + 沉淀使用规范」）：
**第一讲（30 分钟，给所有使用方）：这份东西什么时候不能信**
① 三个必须看的信号：回答里有没有 `[n]` 引用（没有 = 无依据，它自己会拒答，你看到拒答就停）；引用点进去打开的是哪份文档、哪个章节、什么日期（废止制度会出现在引用里吗？这就是你该追问的）；「没有足够信息」是功能不是故障。
② 责任链：你发起的每次问答与每次 Agent 运行都有记录（request_id），出了事我们用它追责，**追责对象是流程里的责任人，不是模型**；
③ 边界清单：它只做检索/分析/只读查询/建议；它**不做**：写业务系统、下控制指令、替审批签字、代替制度文件本身。这条清单我会印进使用规范首页。
**第二讲（给能写文档的人）：怎么把你们的知识喂得对**
- 制度/规程类文档入库前必填三件套：密级、适用范围、生效/废止日期（Q26-03 的 owner 流程，培训里教会他们**谁有责任填这三项**）；
- 常见坑：把「会议纪要」当制度入库（时效性错配）、把废止文件留着（引用污染）、把密码/账号贴进正文（会被全文检索命中）；
- 演示一次「错误文档入库 → 我如何发现并撤出」（双索引 + 撤权即重建，Q7-13）。
**第三讲（给数据 owner / 审计员）：怎么看审计**
- 用哪个字段过滤（`request_id` / 工具 / 用户 / 状态）、401 去哪查（内存事件 + 日志，不是数据库——`[MY DESIGN]` 这是审计与日志的分工）、`denied` 事件该当成什么（需求信号 + 越权尝试，两类含义不同）。
**培训材料的形式**：一页使用规范（可打印）+ 一个可运行的 Demo 账号（operator 视角，让他亲眼看到自己被拒的样子——**被拒过一次的用户比看十页文档的用户信这套系统**）+ 一份 FAQ（「为什么它拒绝回答」「为什么引用点不开」「为什么我的问题被标了 denied」）。
**培训效果的可测指标**（这是我不自欺的部分）：拒答率趋势、点踩率、「文档缺料」类反馈的闭环时间（哪份 FAQ 的反馈促成了新文档入库）。**培训不是讲完就结束，是这个平台有没有「纠错通道」决定的**。

#### Follow-up Questions

- 他们听不懂怎么办？（用一次他们自己的事故场景倒推：「假设上周那份被废止的工艺规程还在库里，你们问的问题答案里出现了它，你能看出差别吗？」——把抽象的「密级/时效」变成可看见的后果）
- 培训谁来做？（平台侧我主讲；领域正确性由安环/工艺侧的 owner 共同讲——**我不能替领域专家讲工艺，他们也不该让我替他们讲**，Q23-07 的边界）

#### Pitfalls

- 不要把培训说成「我给他们开个会」。要说出：课件形态、Demo 账号设计、可测指标、纠错通道，四样。
- 不要承诺「培训完大家就不会误用了」。承诺的是「他们知道什么时候不能信、以及出错了往哪报」。

#### Interview Keywords

`training outcome is knowing when not to trust` `three required fields at ingest` `refusal is a feature demo` `correction channel decides the training's value`

---

# 31 · 快速复习表（面试前 15 分钟 / 候场）

> 只背这张表 + §27.1 数字卡。每张卡片三行：**主张 / 判据 / 证据位置**。

## 31.1 六大技术域（§5–§9）

| # | 卡片 | 主张 | 判据 / 数字 | 证据 |
|---|---|---|---|---|
| 1 | 网关 | 业务代码不许 import provider SDK；provider 注册 = 两个 env 同开；`degraded` 打标 + 默认 false | `LLM_FALLBACK` 默认 false；mock 失败**不再**降级 | `app/gateway/{router,base,mock}.py`；`tests/unit/test_gateway.py`（3 条 fallback 测试） |
| 2 | RAG | 先融合打分再截 top_k 再 min_score；「无依据」是显式拒答不是空回答 | chunk 1000/150，top_k 5，min_score 0.10，over-fetch 4，候选上限 200；语料 6 篇 45 chunk | `app/rag/{retriever,prompt}.py`；拒答话术在 `prompt.py` |
| 3 | Agent | 60 行有限 loop，三个终止态，工具失败是数据不是异常 | max_steps 5（端点上限 20），max_tool_calls 8（端点 ≤20）；终止态 completed/max_steps/max_tool_calls | `app/agent/runtime.py`；`tests/unit/test_agent_runtime.py` |
| 4 | 工具 | 白名单→权限→校验→执行；双视图输出；SQL 是常量 | 4 工具 12 operation；SQL 全在 `queries.py`，零拼接；模型看不到 SQL | `app/agent/executor.py`、`app/db/queries.py` |
| 5 | MCP | 没接；工具面与注册表已是 MCP-ready 形状；治理在平台侧 | 1 宿主 + 4 工具 → 收益不成立 | §10 Q10-05/Q10-06（这是**评估**，不是实现经验） |
| 6 | 企业平台 | 5 层（身份/模型/知识/工具/运维），5 条铁律 | 权限双查、审计集中净化、request_id 全链、降级打标、只读边界 | §11 |

## 31.2 平台能力（§14–§20）

| 卡片 | 主张 / 数字 | 证据 |
|---|---|---|
| RBAC | 3 角色 10 权限；7 路由族 + 3 工具族互不继承；fail-closed | `app/auth/permissions.py`（39 条测试） |
| 审计 | 一行一动作；denylist 净化；401 不落库（`user_id NOT NULL`）；失败不打挂请求 | `app/observability/audit.py`（19 条测试） |
| 可观测 | `/health` + `/metrics`（15 项）+ 结构化日志；**没有**告警规则/分位数 | `app/observability/{middleware,metrics}.py` |
| 错误契约 | 统一信封：`detail` 给人 + `error.code` 给程序；**429 错误码已预留但无生产者** | `app/api/errors.py`（268 行） |
| 安全 | 身份只来自请求；工具白名单；审计不记 prompt；合成数据声明 | §17 五条纪律 |
| Docker | 两容器；语料 `:ro`；`start_period 40s`；nginx 变量 + resolver；无 CORS（同源） | `docker-compose.yml`、`web/nginx.conf` |
| 数据库 | SQLite 9 表；SQL 常量 + 绑定参数；julianday 是迁移时先要换的方言点 | `app/db/queries.py`（36 条测试） |

## 31.3 自审与高危追问（§21/§22/§23）

| 卡片 | 主张 | 备注 |
|---|---|---|
| 9 项修复 | 静默降级、401 泄露 token 形状、审计失败路径、工具 fail-open、内存无界等，**全部有对应测试** | `git show 460a6ee` |
| 修复自己引入 2 缺陷 | `content: str` 重复声明；`clear()` 把有界 deque 换无界 list —— **两处均已修正** | Q21-04 / Q22-04 |
| 文档漂移 3 处 **已修** | README 测试数（该轮修至 422，现为 423）、`app/security/permissions.py` → `app/auth/permissions.py`、合成数据 README 代码 `301109.SZ` → **301118.SZ** | §34 |
| 高危 9 题 | AI 生成？皮？ERP 哪来的？为什么不用 Dify？one-api？没化工背景？没上线过？死模块？ | §23，每题有红线 |
| 不知道怎么办 | 四句结构 + 三档表述（读过/了解/上线过）+ 6 条红线 | §24 |

## 31.4 数字速记（只记这几个）

`423 passed`（约 15s）· `7649` Python 行 · `3133` 前端行 · `6 docs / 45 chunks` · `11 endpoints` · `4 tools / 12 operations` · `3 roles / 10 permissions` · `9 tables` · `8 runtime deps` · `5 defects 自审发现（其中 3 处文档漂移 + 2 处代码缺陷已修）` · `恒光 301118.SZ` · `代码证据基线 460a6ee（当时 420 tests / 7 commits）`。

---

# 32 · 反问环节：我要问面试官的问题

> 反问的作用：① 确认岗位真实状态（避免入职后落差）；② 展示「我按什么标准做技术决策」。每个问题后附「为什么要问」与「听到什么要警惕」。

## Q32-01 关于团队与岗位

| 我要问 | 为什么问 | 警惕信号 |
|---|---|---|
| 「这个岗位是新建还是替补？之前这块事是谁在做、现在在哪个环节？」 | 判断我进来是**搭骨架**还是**接烂尾**（工作量、可预期、权限完全不同） | 「之前的同事离职了，你接过去就行」——接盘时最该问技术债与数据现状，别急着接 |
| 「我直属上级是工程负责人还是业务负责人？技术决策最终归谁？」 | 我 5 天的做法是「架构上把不可逆的定死、可逆的留灵活」，这个原则能不能用，取决于决策链多长 | 上级是「什么都要管」的业务侧 → 我会被拉去做应用层，平台层做不深 |
| 「JD 里写招 1 人，未来 12 个月编制计划？」 | `[FACT]` JD 招 1 人。1 人意味着我同时做选型 + 开发 + 运维 + 文档培训（JD 1、4、6 条）——我要确认可接受度 | 「后面团队会扩，你先顶上」——先顶上的活往往永远不会交出去 |

## Q32-02 关于技术现状

| 我要问 | 为什么问 | 警惕信号 |
|---|---|---|
| 「现在公司里有没有已经在跑的 AI 相关工具（哪怕是员工自用的）？用的是哪家？」 | 决定我「从 0 到 1」还是「治理已存在的野生长点」，两者的第一周动作完全不同 | 「没听说过」但员工已在用某 SaaS → 治理问题比建设问题更优先 |
| 「模型目前跑在什么上面？有没有 GPU？出域政策是谁定的、现在怎么执行？」 | 出域政策是私有化 vs 云端的分水岭，直接影响选型（§26 Q26-04 第 4 步） | 「老板说别用外网的就行」——没有制度只有口号 → 我会主张写进平台使用规范 |
| 「ERP/OA 是谁家的？接口形态（库/服务/文件）大概什么样？有没有只读账号可以给我？」 | 决定「ERP 对接」这一期的真实工作量（Q9-06 的三件确认） | 「你先做，数据库我让你连」——让我连生产库 = 第一周就有事故面 |
| 「现在有没有可用的语料库（制度/规程/SOP）？密级和 owner 是怎么定的？」 | 知识库能不能跑起来 = 语料准入流程能不能建起来（Q26-03） | 「文档都在某某部门，你去找他要」→ 语料会卡死在 owner 流程上，这是最常见的死因 |

## Q32-03 关于成功标准

| 我要问 | 为什么问 | 警惕信号 |
|---|---|---|
| 「前 3 个月您希望我看到什么结果？什么状态算『这个岗位做对了』？」 | 把考核口径提前拿到手，避免我自嗨了 3 个月才发现做反了 | 答不上来 → 说明连负责人自己也没想清楚边界 |
| 「这个平台的第一批真实用户是谁？他们现在最痛的一件事是什么？」 | 让我把「平台能力」对准「第一批用户的痛」，而不是对准「我能讲的技术点」 | 「所有部门都要用」→ 没有第一批用户 = 没有验收方 = 项目会死 |
| 「如果模型给出错误答案，现行流程里这一步由谁负责？」 | 直接考察责任链是否存在（Q23-07 的落地） | 「模型答错了就是模型的问题」→ 责任链不存在，而我要建的核心之一就是它 |

#### Pitfalls

- 反问控制在 3–5 个，按「岗位现状 → 技术现状 → 成功标准」顺序。问完要**记录对方答案**并当场复述确认一次（「您说的是 X，我理解对吗」）。
- 不问薪资（薪资谈判在 §33/offer 环节），不问「加班多不多」（换成「峰值并发与值班安排」——既专业又不显得怕活）。
- 如果对方答不上来，不要替他答。记录问题，写进入职第一周的待确认清单（§12 第二阶段会用到）。

#### Interview Keywords

`confirm the real job, not the written JD` `who owns the data and the out-of-domain policy` `what makes this role a success in 3 months`

---

# 33 · 薪资、offer 与沟通

## Q33-01 薪资怎么谈（`[FACT]` JD 标注 8千–1.2万）

#### Short Answer

先让对方报价，再给区间并说明构成；用「平台价值 + 可验证交付物」支撑，不用「我的能力」。

#### Standard Answer

`[MY DESIGN]` 我的立场（`[需要本人确认：个人底线与期望数字]`）：
① **顺序**：技术面与交叉面不主动提数字；HR 面如果对方先开价，我回「我了解到岗位范围是 8k–1.2w，我更在意整体包（基数/调薪周期/公积金比例/绩效结构），您方便先给一个完整的 offer 构成吗」——**把谈判对象从月薪拉到整包**，这是最便宜的一步。
② **锚点用交付物不用形容词**：「我独立交付了一个 423 个测试、可 Docker 部署、含权限审计网关的统一平台原型；贵司 JD 的九项职责里有七项是它的目录结构。」这句话的价值是**让 HR 有东西可以向上汇报**——HR 谈薪要的是理由，我给她理由。
③ **区间而非单点**：给出 10–1.2w 的区间 + 说明 1.2w 对应什么（例：含私有化部署与模型评测全责）。单点报价只给对方一个砍的点。
④ **可被拒绝的部分提前想好**：到岗时间、驻场、出差、加班费——这些是我「可以答应但需要确认」的清单，而不是「为了拿到 offer 先答应」的清单（§24 红线第 6 条）。
⑤ **拿到书面 offer 前所有口头承诺不算数**。
**不做的三件事**：不用「我不在乎钱」（HR 听到的是「你不好管」）；不贬低前雇主薪资（「我现在 XX，涨 50% 才去」是最差的开场）；不在没拿到书面 offer 前离职/停止其他面试。

#### Pitfalls

- 不要报我记不清的上一份薪资数字（`[需要本人确认]`）。
- 不要说「您看着给」——这等于把决定权让出去。

---

## Q33-02 其他 HR 高频追问（补充 §3）

| 问题 | 标准答法 | 要点 |
|---|---|---|
| 期望工作城市/到岗时间 | `[需要本人确认]`；到岗给**区间**不给死日期，理由留一个客观项（交接） | 不承诺没有权限承诺的事（§24 红线 6） |
| 加班怎么看 | 「我按里程碑排自己的 5 天日程（可指 `git log`），关键路径上愿意加班；常态化 996 我会在入职前确认清」 | 既不拒绝辛苦，也不默认接受 |
| 职业规划 | 1 年：平台稳定运行 + 模型评测体系跑起来（JD 第 5 条）；3 年：带 1–2 人、把平台拆到多基地/多租户形态（§26 Q26-02） | 规划必须挂 JD，不挂 JD 的规划在 HR 眼里等于没想 |
| 为什么选制造业而不是互联网 | 「模型能力正在基础设施化，**把模型接进一家有真实安全与合规约束的制造企业，是我认为当前技术价值密度最高的位置之一**；化工行业的安全红线让『做对的默认值』比『做更多的功能』重要」 | 与 Q2-02/Q13 呼应 |
| 压力大的例子 | §25 Q25-01（审计旁路打挂主请求那条链） | 用可验证的项目事实，不编造 |
| 失败经历 | §25 Q25-04（`clear()` 旁路缺陷） | 有明确发现路径与修正规矩 |

---

# 34 · 文档漂移与事实核对清单

> **这一节是我整理这份材料时实测出来的「仓库里当时就有」的清单**。
> 纪律：以下每条我都给出**核对命令**，任何人（包括面试现场的我）都能重新验证。
> **状态更新**：#1–#5 与 #10 已在「最终一致性修复」提交中关闭（该提交同时新增 2 条回归测试）；#6–#9 仍留档、本轮刻意不修（理由见 §34.1 末尾）。

## 34.1 仓库内发现的不一致（按严重度排序）

| # | 位置 | 现状 | 正确值 | 核对方式 |
|---|---|---|---|---|
| 1 | `README.md`（概览表 / 基线行 / 结构树 / 命令注释） | 旧测试数 `410` | **422**（`uv run pytest --collect-only -q` 实测）—— ✅ **已修** | 同 §27.1 |
| 2 | `README.md`（能力表 + 目录树） | 写 `app/security/permissions.py`（不存在） | 实际路径 `app/auth/permissions.py` —— ✅ **已修** | `ls app/auth/` |
| 3 | `data/synthetic/README.md` + `data/synthetic/seed.json` | 股票代码 **301109.SZ** | 恒光股份为 **301118.SZ**；301109 是「湖南军信环保」—— ✅ **已修**（两处） | 巨潮/上市公告书（§35.2） |
| 4 | `app/gateway/base.py` | `ModelResponse.content: str` 被**声明两次** | 删掉重复行 —— ✅ **已修**（dataclass 字段表已复核，OpenAI-compatible 与 MockProvider 测试全过） | `grep -c "content: str" app/gateway/base.py` → 1 |
| 5 | `app/observability/audit.py::clear` | `self._records = []`（无界 list，绕过 Fix #5 的 deque maxlen） | `self._records.clear()`（deque 原地清空保留 maxlen）—— ✅ **已修** + `TestMemoryBound` 2 条回归测试 | `uv run pytest tests/unit/test_audit.py -q` |
| 6 | `app/services/chat_service.py` | 仅剩文档字符串的死模块 | 删除或恢复其用途 | `wc -c` |
| 7 | `app/api/chat.py::ChatResponse` | `sources`/`tool_calls` 恒空字段 | 删除或让 `mode=agent` 走 AgentService 填充 | §21 Fix #9 |
| 8 | `app/observability/audit.py::AuditAction` | `KNOWLEDGE_DOCUMENTS`/`MODELS_LIST`/`AUDIT_READ` 声明未使用 → 对应三个端点无审计行 | 补三处 `record(...)` 或删常量 | `grep -rn "AuditAction" app/` |
| 9 | `app/auth/permissions.py::_TOOL_PERMISSIONS` vs 各 `Tool.permission` | 工具→权限映射**两处定义**（漂移风险） | 由 `Tool` 派生，删手工表 | §22 #5 |
| 10 | `ruff format --check .` | 曾**不通过**（`tests/integration/test_chat.py` 的格式化差异，源自审计修复提交） | `ruff format .` —— ✅ **已修**，现在 `--check` 全绿 | 命令 |
**处置状态（最终一致性修复提交后）**：#1–#5 与 #10 ✅ 已修（#4/#5 是代码缺陷，各配了验证与回归测试）；#6–#9 仍未修，且**刻意不在本轮修**——#6/#7 是死代码与恒空字段的删除决策、#8 要给三个只读端点补审计写入（等于改行为）、#9 是权限映射的派生重构，四者都需要先有测试护航，不属于「文档一致性」范围。分类不变：1–3 事实性错误、4–7 代码卫生、8–10 观测/一致性缺口。**
**已执行的处置**：1–5 与 10 在 `fix: close final documentation and consistency drift` 里关闭（#4/#5 属代码缺陷，各配了复核与回归测试）。**仍建议但本轮未做**：6–7 二选一（我倾向删 `chat_service.py`、删 `ChatResponse` 恒空字段——项目纪律是不保留为兼容而留的尸体，但删字段是行为决策，要先有契约测试护航）；8–9 配负例测试后再做。

## 34.2 本材料里我刻意保留的「不确定」（不修的理由）

- 恒光当前在用的 ERP/OA 品牌：公开信息不足以确定 → 全部标 `[INFERENCE]`，入职第一周确认（§23 Q23-03 纪律）；
- 面试当天的薪资底线、到岗时间：个人事实 → `[需要本人确认]`（§33）；
- 我的 5 天项目里是否使用 AI 辅助工具的具体范围：`[需要本人确认]`（§23 Q23-01 的诚实模板依赖本人填）。

---

# 35 · 来源

> 检索时间均为 **2026-10-01**。仓库类来源可本地复核；公开网络类来源以官方/准官方渠道为准，本文**不引用未核实的数字**（榜单排名、产品 star 数、定价均无）。

## 35.1 仓库内（可本地验证）

| 内容 | 位置 |
|---|---|
| 架构与边界 | `ARCHITECTURE.md`（133 行） |
| 本期范围与禁止清单 | `SPEC.md` §0（1714 行） |
| 快速开始 / 已知限制 / 测试基线（与实测一致） | `README.md`（246 行） |
| 演示六步 | `DEMO_SCRIPT.md`（72 行） |
| 测试实测 | `uv run pytest -q` → `423 passed, 2 warnings`（约 15s） |
| 静态检查实测 | `uv run ruff check .` PASS；`uv run ruff format --check .` **PASS** |
| 自审提交 | `git log -1` → `460a6ee fix: address audit security and reliability findings` |
| 合成数据与语料声明 | `data/synthetic/README.md`、`data/documents/README.md` |
| 截图 | `screenshots/`（6 张，随 README） |

## 35.2 公司公开信息（`[FACT]`，检索 2026-10-01）

- **湖南恒光科技股份有限公司**，统一社会信用代码 91430500MA4L5Q6G27，2008-06-19 成立（2015-08-18 整体变更为股份公司，注册资本 31680 万元）。
- 2021-10 创业板上市，股票代码 **301118.SZ**（来源：上市公告书 / 巨潮资讯网）。
- 主营：氯碱、硫酸等硫氯系列精细化工品，**电子级磷酸、磷酸铁锂用磷酸铁**；「硫—氯—磷」产业链 + 光伏新材料（磷酸铁/电子级磷酸）。
- 基地：湖南衡阳（本部）、湖南邵阳、云南玉溪等；境外 **老挝**（恒光新材老挝项目，电子级磷酸）。
- 子公司：云南玉溪恒光新能源、上海恒光电子材料、老挝恒光新材、湖北新昌达（恒光新材料湖北）等。
- 2025 年度报告：营业总收入 **约 54.96 亿元**；归母净利润 **亏损（约 -0.32 亿元，即首次年度亏损）**；总资产约 40.4 亿元；电子级磷酸收入占比约 19.16%（来源：公司 2025 年年度报告摘要，公开转载口径；具体科目以年报原文为准）。
- 行业关键词：精细化工 / 电子化学品 / 新能源材料 / 磷化工 / 氯碱；「工业互联网 + 危化安全生产」相关政策与行业背景（行业层面事实，非恒光专属项目承诺）。
- **301109.SZ 不是恒光股份**：301109 是「湖南军信环保股份有限公司」（2022-03-31 上市，来源为交易所公开代码表）。本仓库 `data/synthetic/README.md` 与 `seed.json` 原先误用该代码指代恒光，**已在最终一致性修复提交中改为 301118.SZ**（见 §34 #3）。

## 35.3 岗位 JD（`[FACT]`，检索 2026-10-01）

- 「AI 平台工程师」，湖南恒光科技股份有限公司，湖南·衡阳（石鼓区），本科，招 1 人，8k–12k。
- 职责 6 条（原文摘录于 §2 顶部）：① 私有化 AI 平台技术选型/架构设计/从 0 到 1 搭建（模型网关、知识库/RAG、Agent 工作流、内部系统集成）；② 持续研究开源 LLM 应用生态（Dify、RAGFlow、FastGPT、One-API/New-API、MCP 协议等）并评估引入；③ 完成平台与内部系统（ERP、OA 等）对接，保障数据安全与流程自动化；④ 平台日常运维、监控、性能优化与故障处理；⑤ 跟进各类大模型（国内外闭源/开源）接入、评测与切换，结合成本和效果优化选型；⑥ 编写技术文档、沉淀平台使用规范，培训支持内部业务部门使用 AI 平台。
- 任职要求（可见部分）：计算机/软件工程相关本科（条件优秀者可放宽）；扎实编程基础（Python/Go/Node.js 任一）+ Docker、Linux 服务器部署运维经验；对大模型、AI Agent、…（JD 原文剩余条目面试前需以官方发布为准）。
- JD 快照出处为公开招聘平台的岗位页，**原文剩余条目未完整抓取**——面试前以官方发布为准（已在 §2 与 §3 标注）。

## 35.4 技术与协议（`[INFERENCE]`，仅定位，非生产经验）

- MCP（Model Context Protocol）：标准化 AI 应用访问工具/数据/资源的开放协议；工具定义 + JSON Schema + 传输层（stdio/HTTP）。定位与用法评估见 §10，**本项目未实现**，全部标注为评估。
- Dify / RAGFlow / FastGPT / One-API / New-API：定位判断见 §28 Q28-02，**均为公开文档阅读结论，未在任何生产环境使用**，具体能力以当前版本文档为准。
- pgvector / Ollama / vLLM / Redis 等：均为 `[PRODUCTION_NEXT]` 候选项，**无生产使用经验**，只在 §5/§20/§26 的「触发条件」中出现。

## 35.5 本材料自身的诚实边界（务必让面试官看到）

- 我**没有**化工行业生产系统经验、**没有**真实 ERP 对接经验、**没有** GPU/私有推理运维经验、**没有**这个平台的监控/告警生产配置（只有指标端点）。
- 所有 `恒光内部现状`（用什么系统、出域政策、数据现状）为 `[INFERENCE]` 或未确认，入职第一周核对。
- 数字类主张只报可本地复核者：423 tests / 约 15s / 7649 行 / 6 docs / 45 chunks / 9 tables / 4 tools / 12 operations / 11 endpoints（代码证据基线 `460a6ee` 时另记 420 tests / 7 commits）。

---

# 36 · 最终报告：这份材料是什么、不是什么

## 36.1 交付物

- `docs/interview/HENGGUANG_INTERVIEW_GUIDE.md`（本文件）：37 个章节（§0–§36），按 §0.1 的路径可分三天复习完；
- `docs/interview/index.html`：同一内容的**自包含**离线 HTML（无 CDN / 无框架），带搜索、按标签过滤（FACT/INFERENCE/MY DESIGN/PRODUCTION_NEXT/需要本人确认）、按章节折叠，用于候场与通勤复习；
- 本指南的**材料提交**（`d1cae32`）不改业务代码，只把 §34 的缺陷记录在案。随后的**最终一致性修复提交**关闭了其中 6 项（#1–#5、#10：文档漂移、`content: str` 重复声明、`AuditLog.clear()` 的 deque 退化、`ruff format`），并新增 2 条回归测试；#6–#9 仍留档未修（理由见 §34.1 的处置状态）。

## 36.2 我承诺读者（未来的我自己）的三件事

1. **每一处 `[FACT]` 都能在 §35 里找到出处与检索时间**；找不到出处的内容我标了 `[INFERENCE]` 或 `[需要本人确认]`。
2. **每一处「我做过」都可以用一条命令或一个文件路径复核**（§27 是索引）；复核不了的我写成了 `[PRODUCTION_NEXT]`（建议）或 §24（不知道怎么办）。
3. **这份材料本身也遵守它教的内容**：它的每个小节都有 Short Answer（可背的 20 秒版）+ Standard Answer（可展开版）+ Follow-up + Pitfalls + Keywords——**如果某个小节我只写了「标准答案」而没有 Pitfalls，请把它当作我没有想清楚的地方，面试前补上。**

## 36.3 面试前 24 小时动作清单

- [ ] `uv run pytest -q`（约 15s，423）；`uv run ruff check .` 与 `uv run ruff format --check .`（均应 PASS）；`docker compose up --build` 走一遍 `DEMO_SCRIPT.md` 六步；
- [ ] 把 `[需要本人确认]` 全部填完（姓名/学历/年限、薪资底线、到岗时间、AI 工具使用说明、前雇主事实、GPU 经验有无）；
- [ ] §34 的 10 条：#1–#5 与 #10 已在最终一致性修复提交里关闭；面试前只需复核这张表，并决定 #6–#9 是否开新提交；
- [ ] 背：§31 全表 + §1（60s/90s 两版）+ §23 九题的 Short Answer + §24 四句模板；
- [ ] 打印：§27.1 数字卡 + §35.2 公司事实卡（**含 301118.SZ 的正确代码**）；
- [ ] 准备录屏一份（六步演示 + 一次越权被拒 + 一次审计追溯），防现场环境故障。

## 36.4 本材料的已知缺陷（自评）

- §11/§26/§28 里的生产化方案**没有一条被验证过**，全部是判据与触发条件（这是刻意设计：不验证的建议只配写成判据）；
- §35.2 的财务数字来自年报摘要的公开转载口径，**科目级数字未在原文核对**（已标注）；
- 全材料**没有**任何真实用户/生产数据支撑的效果结论；所有「检索质量好/Agent 稳定」的表述都限定在「423 个行为测试」之内（§7 Q7-12 的口径）；
- 本材料 2026-10-01 之后若 `HEAD` 前进，§34 的核对命令结果可能变化——**复核 §27 与 §34 只需 5 分钟，先于阅读正文**。
