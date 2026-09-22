# Knowledge Base — Public Documents Only

This directory holds the RAG knowledge base for the demo.

## Rules (SPEC section 6.1)

- **Only public materials are allowed**: public company profile, public annual /
  half-year reports, public news, public product / technology / safety materials.
- No internal Hengguang systems, no internal data, accounts, keys, business
  data or unpublished materials.
- Every ingested document must carry metadata:

```json
{
  "document_id": "hg-annual-report-2025",
  "title": "2025年年度报告",
  "source": "public",
  "url": "https://...",
  "page": 123,
  "section": "公司业务",
  "published_at": "2026-..."
}
```

If a URL is unstable, save the legitimately downloaded public file here and
record the original URL in the metadata.

## Contents

- `hengguang_public_profile.md` — public company profile used by the demo
- `public_reports/` — public reports / news / product materials
