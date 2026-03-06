# Example files | 示例文件

Sample documents for testing Arthor Agent locally.  
用于本地测试 Arthor Agent 的示例文档。

| File | Use |
|------|-----|
| **sample.txt** | Minimal "security questionnaire" for testing the assessment API. Use with `curl -F "files=@sample.txt"` or via Swagger `/docs`. |
| **sample-policy.txt** | Short policy excerpt for testing KB upload and RAG query (`/api/v1/kb/documents`, then `/api/v1/kb/query`). |

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
