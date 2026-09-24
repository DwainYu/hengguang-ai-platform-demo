# Knowledge Base — Public Documents Only

This directory holds the RAG knowledge base for the demo.

## Rules (SPEC section 6.1)

- **Only public materials are allowed**: public company profile, public annual /
  half-year reports, public news, public product / technology / safety materials.
- No internal Hengguang systems, no internal data, accounts, keys, business
  data or unpublished materials.
- Markdown / TXT 文档用 YAML front matter 声明 metadata（ingest 时解析）：

```markdown
---
document_id: hengguang-annual-report-2025
title: 恒光股份 2025 年年度报告（公开披露要点整理）
source: public
url: https://static.cninfo.com.cn/...
published_at: 2026-04-28
---
```

- 缺省字段自动回退：`document_id` = 文件名，`title` = 第一个 `#` 标题，`source` = `public`；
  `section` 由 ingest 时按 Markdown heading / PDF 页码自动生成。
- PDF（pypdf 按页提取）无法内嵌 metadata，建议放同名 `.md` 摘要或在 metadata 中记录原始 URL。
- URL 不稳定时，可在 repo 中保存合法下载得到的公开文件，并在 metadata 中记录原始 URL。

## Contents

- `hengguang_public_profile.md` — 公司公开简介（官网关于我们 + 基地介绍）
- `public_reports/hengguang_annual_report_2025.md` — 2025 年年度报告公开披露要点
- `public_reports/hengguang_half_year_report_2026.md` — 2026 年半年度报告公开披露要点
- `public_reports/hengguang_products_and_capacity.md` — 主要产品、产能与基地分布（公开年报口径）
- `public_news/hengguang_ipo_2021.md` — 2021 年登陆创业板公开报道摘要
- `public_news/hengguang_safety_production_2025.md` — 安全环保、智能工厂与公开公告汇编

## Ingest

```bash
curl -X POST http://localhost:8000/api/knowledge/ingest \
  -H 'Content-Type: application/json' -d '{}'
```

- `README.md` 与不支持的文件类型自动跳过；重复 ingest 会替换同一 `document_id` 的旧 chunks。
- 所有 chunk 保留 document_id / title / section / page / source / url / published_at，
  检索结果据此生成 `[n]` 引用。
