# Contributing to Arthor Agent | 参与贡献

Thank you for your interest in contributing. We welcome issues, pull requests, and feedback.

感谢你对 Arthor Agent 的关注。我们欢迎提交 Issue、Pull Request 以及任何反馈。

---

## 中文

### 如何参与

1. **报告问题或建议功能**：在 [Issues](https://github.com/arthurpanhku/Arthor-Agent/issues) 中新建 Bug 报告或功能建议，使用模板并尽量提供复现步骤或使用场景。
2. **提交代码**：Fork 本仓库，在本地创建分支，修改后提交 PR 到 `main`。请先阅读下方「开发环境」与「提交规范」。
3. **文档与示例**：改进 README、SPEC、注释或补充示例同样欢迎。

### 开发环境

- **Python 3.10+**
- 推荐使用虚拟环境：
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate   # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt   # 测试与开发依赖
  ```
- 或使用 **Docker**：`docker compose up -d` 仅启动 API；需要容器内 Ollama 时使用 `docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d`。

### 运行测试

请确保在**已激活本项目虚拟环境**的情况下运行（否则会报 `No module named 'fastapi'` 等）：

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pytest
# 或带覆盖率
pytest --cov=app --cov-report=term-missing
```

不激活时也可用：`./.venv/bin/python -m pytest`

- 测试不依赖真实 LLM（Ollama/OpenAI），通过 mock 完成。
- CI 在每次 push/PR 时自动运行测试（见 `.github/workflows/ci.yml`）。

### 提交规范

- **Commit message**：简短清晰，如 `feat: add X`、`fix: resolve Y`、`docs: update Z`。可选遵循 [Conventional Commits](https://www.conventionalcommits.org/)。
- **PR**：请填写 PR 模板（改了什么、如何验证、是否更新文档）。若对应 Issue，在描述中注明并链接。
- **代码风格**：保持与现有代码一致；可选使用 [Black](https://github.com/psf/black) 格式化 Python 代码。

### 分支与发布

- 主开发分支为 **`main`**。
- 发版通过 **Git tag**（如 `v0.1.0`）与 [GitHub Releases](https://github.com/arthurpanhku/Arthor-Agent/releases) 完成；版本说明见 [CHANGELOG.md](CHANGELOG.md)。

---

## English

### How to contribute

1. **Report bugs or suggest features**: Open a new [Issue](https://github.com/arthurpanhku/Arthor-Agent/issues) using the Bug report or Feature request template; include steps to reproduce or use case when possible.
2. **Submit code**: Fork the repo, create a branch, make your changes, and open a Pull Request to `main`. See « Development setup » and « Commit guidelines » below.
3. **Docs and examples**: Improvements to README, SPEC, code comments, or examples are welcome.

### Development setup

- **Python 3.10+**
- Recommended: use a virtual environment:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate   # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt   # Test and dev dependencies
  ```
- Or use **Docker**: `docker compose up -d` runs only the API; use `docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d` if you need Ollama in Docker.

### Running tests

Make sure you run tests **with the project venv activated** (otherwise you may see `No module named 'fastapi'`):

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pytest
# Or with coverage
pytest --cov=app --cov-report=term-missing
```

Without activating: `./.venv/bin/python -m pytest`

- Tests do not require a real LLM (Ollama/OpenAI); they use mocks.
- CI runs tests on every push/PR (see `.github/workflows/ci.yml`).

### Commit guidelines

- **Commit messages**: Short and clear, e.g. `feat: add X`, `fix: resolve Y`, `docs: update Z`. Optionally follow [Conventional Commits](https://www.conventionalcommits.org/).
- **PRs**: Please fill in the PR template (what changed, how to verify, docs updated or not). If related to an Issue, reference it in the description.
- **Code style**: Match existing style; optionally use [Black](https://github.com/psf/black) for Python formatting.

### Branching and releases

- The main development branch is **`main`**.
- Releases are made via **Git tags** (e.g. `v0.1.0`) and [GitHub Releases](https://github.com/arthurpanhku/Arthor-Agent/releases); release notes are in [CHANGELOG.md](CHANGELOG.md).
