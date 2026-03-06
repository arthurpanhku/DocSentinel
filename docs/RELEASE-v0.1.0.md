# Arthor Agent v0.1.0 — Release notes

**Release title (GitHub)**：`v0.1.0` 或 `v0.1.0: First release — Assessment API, RAG, Docker`

---

将以下内容复制到 GitHub → Releases → Draft a new release → 选择 tag `v0.1.0` → 粘贴到描述框。  
Copy the content below into GitHub → Releases → Draft a new release → choose tag `v0.1.0` → paste into the description.

---

## 中文

这是 **Arthor Agent** 的首个正式版本，面向安全团队的 AI 评估助手：上传文档与问卷，结合知识库与策略，产出结构化评估报告（风险、合规差距、整改建议）。

### 本版本包含

- **评估 API**：提交 PDF、Word、Excel、PPT、文本，获得结构化报告（风险项、合规差距、整改建议）。
- **知识库（RAG）**：上传策略/合规文档，分块与向量化（Chroma），支持检索接口。
- **多格式解析**：PDF（PyMuPDF）、Word（python-docx）、Excel（openpyxl）、PPT（python-pptx）、纯文本/Markdown。
- **LLM 抽象**：支持 OpenAI 与 Ollama（本地），通过 `LLM_PROVIDER` 与环境变量配置。
- **REST API**：FastAPI，提供 `/api/v1/assessments`、`/api/v1/kb/documents`、`/api/v1/kb/query`、`/health`；Swagger 文档在 `/docs`。
- **Docker**：`Dockerfile` 与 `docker-compose.yml`，一键启动 API 与可选 Ollama 服务。
- **文档**：SPEC、ARCHITECTURE.md、设计文档 01–05、SECURITY.md、中英双语 README 与快速开始。

### 使用本发布包（ZIP）

1. 下载本 Release 的 **Source code (zip)**（或你自行打包的 zip）。
2. 解压到本地目录。
3. **Docker 方式**（推荐）：
   ```bash
   cd Arthor-Agent-0.1.0   # 或你解压后的目录名
   docker compose up -d
   # 浏览器打开 http://localhost:8000/docs
   docker compose exec ollama ollama pull llama2
   ```
4. **Python 方式**：需 Python 3.10+，解压后执行：
   ```bash
   cd Arthor-Agent-0.1.0
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 说明

- 当前任务状态为内存存储（MVP），生产环境建议替换为 DB/Redis。
- AAD、ServiceNow 等集成在规划中，详见 SPEC 与 `docs/04-integration-guide.md`。

完整变更见 [CHANGELOG.md](https://github.com/arthurpanhku/Arthor-Agent/blob/main/CHANGELOG.md)。

---

## English

This is the **first official release** of **Arthor Agent**, an AI-powered assistant for security teams: upload documents and questionnaires, compare against your knowledge base and policies, and get structured assessment reports (risks, compliance gaps, remediations).

### What’s in this release

- **Assessment API**: Submit PDF, Word, Excel, PPT, or text and receive structured reports (risk items, compliance gaps, remediations).
- **Knowledge base (RAG)**: Upload policy/compliance documents; chunking and embedding with Chroma; query endpoint for retrieval.
- **Multi-format parser**: PDF (PyMuPDF), Word (python-docx), Excel (openpyxl), PPT (python-pptx), plain text/Markdown.
- **LLM abstraction**: Support for OpenAI and Ollama (local); configurable via `LLM_PROVIDER` and environment variables.
- **REST API**: FastAPI with `/api/v1/assessments`, `/api/v1/kb/documents`, `/api/v1/kb/query`, `/health`; Swagger at `/docs`.
- **Docker**: `Dockerfile` and `docker-compose.yml` for one-command run with optional Ollama service.
- **Documentation**: SPEC, ARCHITECTURE.md, design docs (01–05), SECURITY.md, bilingual README (CN/EN) with Quick Start.

### Using this release (ZIP)

1. Download the **Source code (zip)** from this release (or your own zip).
2. Extract to a local folder.
3. **Docker** (recommended):
   ```bash
   cd Arthor-Agent-0.1.0   # or your extracted folder name
   docker compose up -d
   # Open http://localhost:8000/docs in your browser
   docker compose exec ollama ollama pull llama2
   ```
4. **Python**: Requires Python 3.10+. After extracting:
   ```bash
   cd Arthor-Agent-0.1.0
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Notes

- Task store is in-memory (MVP); use a DB/Redis for production.
- AAD and ServiceNow integrations are planned; see SPEC and `docs/04-integration-guide.md`.

Full changelog: [CHANGELOG.md](https://github.com/arthurpanhku/Arthor-Agent/blob/main/CHANGELOG.md).
