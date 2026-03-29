# 05 — Deployment and Runbook | 部署与运行手册

|                 |                                                              |
| :-------------- | :----------------------------------------------------------- |
| **Status**      | [ ] Draft \| [ ] In Review \| [ ] Approved                   |
| **Version**     | 0.3                                                          |
| **Related PRD** | Section 7 Non-Functional Requirements (Deployment, Security) |

---

## 1. Environment Requirements | 环境要求

### 1.1 Runtime

| Item       | Requirement                                             |
| :--------- | :------------------------------------------------------ |
| **Python** | 3.10+                                                   |
| **OS**     | Linux (Recommended) / Windows Server / Container        |
| **Memory** | Minimum 4GB, Recommended 8GB+ (for local LLM/Vector DB) |
| **CPU**    | 2+ Cores (AVX support for some vector libs)             |
| **Disk**   | SSD recommended for Vector DB I/O                       |

### 1.2 Dependent Services

| Service          | Usage                                    | Required             |
| :--------------- | :--------------------------------------- | :------------------- |
| **Vector DB**    | Knowledge Base retrieval (Chroma/Qdrant) | Yes                  |
| **LLM Endpoint** | OpenAI / Ollama / Claude / Qwen          | Yes                  |
| **Redis**        | Session/Cache (Optional for MVP)         | Optional             |
| **PostgreSQL**   | Task/User data (Future)                  | Optional             |
| **AAD**          | Identity & SSO                           | Recommended for Prod |

---

## 2. Deployment Options | 部署方式

### 2.1 One-Click Deployment (Recommended) | 一键部署（推荐）

Suitable for Development, PoC, or Small Teams. Includes API and optional Ollama.

```bash
# Clone repo
git clone https://github.com/arthurpanhku/DocSentinel.git
cd DocSentinel

# Run script
chmod +x deploy.sh
./deploy.sh
```

- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2.2 Docker Manual | 容器化手动部署

See `Dockerfile` and `docker-compose.yml` in repo.

**Compose Example**:
```yaml
services:
  agent:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes: ["./data:/app/data"]
```

### 2.3 Python Standalone | Python 单机部署

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2.3 Air-Gapped / Private Cloud | 内网/私有化

For environments without public internet access:
1.  **LLM**: Use **Ollama** or **vLLM** deployed internally.
2.  **Identity**: Use local accounts or internal IdP (LDAP/AD) if AAD is unreachable.
3.  **Dependencies**: Mirror PyPI packages or use pre-built Docker images.

---

## 3. Verify Installation | 验证安装

### 3.1 Automated Verification (Recommended)

Run the integration test script to verify core functions (API, Skills, Orchestrator) in an isolated environment:

```bash
./test_integration.sh
```

### 3.2 Manual Check

After deployment, you can run a quick self-check using `pytest` (requires python environment):

```bash
# Install test deps
pip install -r requirements-dev.txt

# Run integration tests against your local instance (mocking LLM)
pytest tests/test_health.py tests/test_assessments_api.py
```

If you see `PASSED`, the core API and orchestration logic are working correctly.

---

## 4. Configuration Reference | 配置项清单

See `.env.example` for the template.

### 3.1 App & API

| Variable          | Description      | Example                  |
| :---------------- | :--------------- | :----------------------- |
| `ENV`             | Environment      | `production`             |
| `LOG_LEVEL`       | Logging level    | `INFO`                   |
| `API_PREFIX`      | API path prefix  | `/api/v1`                |
| `SECRET_KEY`      | Session/Sign key | *Random String*          |
| `ALLOWED_ORIGINS` | CORS origins     | `https://ui.example.com` |

### 3.2 Authentication (AAD)

| Variable            | Description     |
| :------------------ | :-------------- |
| `AAD_TENANT_ID`     | Azure Tenant ID |
| `AAD_CLIENT_ID`     | App Client ID   |
| `AAD_CLIENT_SECRET` | Client Secret   |
| `AAD_REDIRECT_URI`  | OIDC Callback   |

### 3.3 LLM Provider

| Variable          | Description    | Example                  |
| :---------------- | :------------- | :----------------------- |
| `LLM_PROVIDER`    | Backend choice | `openai` / `ollama`      |
| `OPENAI_API_KEY`  | Key for OpenAI | `sk-...`                 |
| `OLLAMA_BASE_URL` | Local LLM URL  | `http://localhost:11434` |
| `OLLAMA_MODEL`    | Model name     | `llama3`                 |

### 3.4 Vector Store

| Variable             | Description       | Example            |
| :------------------- | :---------------- | :----------------- |
| `CHROMA_PERSIST_DIR` | Data path         | `./data/chroma`    |
| `EMBEDDING_MODEL`    | HuggingFace model | `all-MiniLM-L6-v2` |

### 3.5 Limits

| Variable                  | Description       | Default |
| :------------------------ | :---------------- | :------ |
| `UPLOAD_MAX_FILE_SIZE_MB` | Max file size     | 50      |
| `UPLOAD_MAX_FILES`        | Max files per req | 10      |

### 3.6 Parser Engine

| Variable        | Description                    | Default |
| :-------------- | :----------------------------- | :------ |
| `PARSER_ENGINE` | `auto`, `docling`, or `legacy` | `auto`  |

### 3.7 Graph RAG (LightRAG)

| Variable               | Description                           | Default           |
| :--------------------- | :------------------------------------ | :---------------- |
| `ENABLE_GRAPH_RAG`     | Enable graph-based retrieval          | `true`            |
| `LIGHTRAG_WORKING_DIR`   | LightRAG data directory               | `./data/lightrag` |
| `GRAPH_RAG_QUERY_MODE`   | Query mode: naive/local/global/hybrid | `hybrid`          |

---

## 4. Operations and Monitoring | 运维与监控

### 4.1 Health Checks

-   **Liveness**: `GET /health` (Returns 200 OK)
-   **Readiness**: `GET /health/ready` (Checks DB/Vector connection)

### 4.2 Logging

-   **Format**: JSON or Text (Standard Output).
-   **Privacy**: **Do not log** sensitive document content or full user tokens.
-   **Fields**: Request ID, User ID, Task ID, Duration, Error Stack.

### 4.3 Auditing

-   **Scope**: Who initiated assessment? Who accessed reports?
-   **Retention**: Comply with organization policy (e.g. 90 days).

### 4.4 Backup

-   **Vector DB**: Backup the `CHROMA_PERSIST_DIR` regularly.
-   **Config**: Backup `.env` (securely).

---

## 5. Troubleshooting | 常见问题排错

| Issue                    | Possible Cause             | Suggestion                                                 |
| :----------------------- | :------------------------- | :--------------------------------------------------------- |
| **Login Loop / 401**     | AAD Config mismatch        | Check Client ID, Secret, and Redirect URI in Azure Portal. |
| **Task Pending Forever** | Worker stuck / LLM timeout | Check logs for LLM connection errors or parser hangs.      |
| **Empty KB Results**     | Embeddings mismatch        | Ensure ingestion and query use the same embedding model.   |
| **ServiceNow Error**     | Network / Auth             | Verify instance URL reachability and credentials.          |

---

## 6. Changelog | 修订记录

| Version | Date    | Changes                       |
| :------ | :------ | :---------------------------- |
| **0.1** | Initial | Draft Deployment and Runbook. |
