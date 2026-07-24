# Example files | 示例文件

Sample documents for testing DocSentinel locally.
用于本地测试 DocSentinel 的示例文档。

| File | Use |
|------|-----|
| **sample.txt** | Minimal "security questionnaire" for testing the assessment API. Use with `curl -F "files=@sample.txt"` or via Swagger `/docs`. |
| **sample-policy.txt** | Short policy excerpt for testing KB upload and RAG query (`/api/v1/kb/documents`, then `/api/v1/kb/query`). |
| **evidence-critic-architecture.md** | Public-demo design document with supported, contradicted, and insufficient-evidence STRIDE scenarios for the inference-time Evidence Critic. |

## Threat Evidence Critic demo

1. Start the API and React console, then open `/console/assessments`.
2. Upload `examples/evidence-critic-architecture.md`.
3. Select phase `design`, skill `SSDLC Design Agent`, and enable human review.
4. Open the completed assessment. The **Threat Evidence Critic** panel shows each
   threat's verdict, support score, exact document line locator, source excerpt,
   and human-review requirement.

The critic uses the configured runtime model and the uploaded document only. It
does not require fine-tuning or a training dataset. If verification fails, every
unverified threat safely falls back to `insufficient_evidence`.

## Quick test (from repo root)

```bash
# Assessment (after starting API: docker compose up -d or uvicorn)
curl -X POST "http://localhost:8000/api/v1/assessments" \
  -F "files=@examples/sample.txt" \
  -F "scenario_id=default"

# KB upload + query
curl -X POST "http://localhost:8000/api/v1/kb/documents" -F "file=@examples/sample-policy.txt"
curl -X POST "http://localhost:8000/api/v1/kb/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the access control requirements?", "top_k": 5}'
```

For PDF, Word, or Excel, use your own files or create minimal test documents; the parser supports `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.md`.
