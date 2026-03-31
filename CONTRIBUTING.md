# Contributing to DocSentinel | 参与贡献

Thank you for your interest in contributing to DocSentinel — an AI-powered SSDLC platform built on LangChain and LangGraph. We welcome issues, pull requests, and feedback.

感谢你对 DocSentinel 的关注——这是一个基于 LangChain 和 LangGraph 构建的 AI 驱动 SSDLC 平台。我们欢迎提交 Issue、Pull Request 以及任何反馈。

---

## English Version | 英文版

### How to contribute

1.  **Report bugs or suggest features**: Open a new [Issue](https://github.com/arthurpanhku/DocSentinel/issues) using the Bug report or Feature request template; include steps to reproduce or use case when possible.
2.  **Submit code**: Fork the repo, create a branch, make your changes, and open a Pull Request to `main`. See "Development setup" and "Commit guidelines" below.
3.  **Docs and examples**: Improvements to README, SPEC, ARCHITECTURE, code comments, or examples are welcome.
4.  **SSDLC Skills**: Submit new phase-specific skills (personas) for any of the 6 SSDLC phases. See "Submit a Skill" below.

### Development setup

-   **Python 3.10+**
-   Recommended: use a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    make install                # Install all dependencies (includes LangChain, LangGraph)
    pre-commit install          # Install git hooks
    ```
-   **Key dependencies**: LangGraph (agent orchestration), LangChain (LLM abstraction), FastAPI (API), ChromaDB (vector store), Docling (parser).
-   **MCP Development**:
    To test the MCP server, install in editable mode:
    ```bash
    pip install -e .
    docsentinel-mcp --help
    ```

### Running tests

Make sure you run tests **with the project venv activated**:

```bash
make test                   # Run tests
make lint                   # Check code style
```

-   Tests do not require a real LLM (Ollama/OpenAI); they use mocks.
-   CI runs tests on every push/PR (see `.github/workflows/ci.yml`).

### Commit guidelines

-   **Commit messages**: Short and clear, e.g. `feat: add X`, `fix: resolve Y`, `docs: update Z`. Optionally follow [Conventional Commits](https://www.conventionalcommits.org/).
-   **PRs**: Please fill in the PR template (what changed, how to verify, docs updated or not). If related to an Issue, reference it in the description.
-   **Code style**: Match existing style; optionally use [Black](https://github.com/psf/black) for Python formatting.

### Submit a Skill

Have a great security persona for an SSDLC phase? We welcome contributions:

1.  Create a skill JSON following the schema in [docs/03-assessment-report-and-skill-contract.md](docs/03-assessment-report-and-skill-contract.md).
2.  Tag it with the appropriate `ssdlc_phase` (requirements, design, development, testing, deployment, operations).
3.  Submit via [Skill Template Issue](https://github.com/arthurpanhku/DocSentinel/issues/new?template=new_skill_template.md) or add to `examples/templates/`.

### Branching and releases

-   The main development branch is **`main`**.
-   Releases are made via **Git tags** (e.g. `v4.0.0`) and [GitHub Releases](https://github.com/arthurpanhku/DocSentinel/releases); release notes are in [CHANGELOG.md](CHANGELOG.md).

---

## Chinese Version | 中文版

### 如何参与

1.  **报告问题或建议功能**：在 [Issues](https://github.com/arthurpanhku/DocSentinel/issues) 中新建 Bug 报告或功能建议，使用模板并尽量提供复现步骤或使用场景。
2.  **提交代码**：Fork 本仓库，在本地创建分支，修改后提交 PR 到 `main`。请先阅读下方「开发环境」与「提交规范」。
3.  **文档与示例**：改进 README、SPEC、ARCHITECTURE、注释或补充示例同样欢迎。
4.  **SSDLC 技能**：为 6 个 SSDLC 阶段中的任何一个提交新的阶段专用技能（角色）。见下方「提交 Skill」。

### 开发环境

-   **Python 3.10+**
-   推荐使用虚拟环境：
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    make install                # 一键安装所有依赖（含 LangChain、LangGraph、开发依赖）
    pre-commit install          # 安装 Git 提交钩子
    ```
-   **核心依赖**：LangGraph（Agent 编排）、LangChain（LLM 抽象）、FastAPI（API）、ChromaDB（向量库）、Docling（解析器）。
-   **MCP (Model Context Protocol) 开发**：
    调试 MCP Server 时，建议使用 `docsentinel-mcp` 命令行工具：
    ```bash
    pip install -e .            # 以编辑模式安装当前包
    docsentinel-mcp --help      # 验证安装
    ```

### 运行测试

请确保在**已激活本项目虚拟环境**的情况下运行：

```bash
make test                   # 运行测试
make lint                   # 检查代码风格
```

-   测试不依赖真实 LLM（Ollama/OpenAI），通过 mock 完成。
-   CI 在每次 push/PR 时自动运行测试（见 `.github/workflows/ci.yml`）。

### 提交规范

-   **Commit message**：简短清晰，如 `feat: add X`、`fix: resolve Y`、`docs: update Z`。可选遵循 [Conventional Commits](https://www.conventionalcommits.org/)。
-   **PR**：请填写 PR 模板（改了什么、如何验证、是否更新文档）。若对应 Issue，在描述中注明并链接。
-   **代码风格**：保持与现有代码一致；可选使用 [Black](https://github.com/psf/black) 格式化 Python 代码。

### 提交 Skill

如果你有适用于某个 SSDLC 阶段的安全角色，欢迎贡献：

1.  按照 [docs/03-assessment-report-and-skill-contract.md](docs/03-assessment-report-and-skill-contract.md) 中的 Schema 创建 Skill JSON。
2.  标注对应的 `ssdlc_phase`（requirements、design、development、testing、deployment、operations）。
3.  通过 [Skill Template Issue](https://github.com/arthurpanhku/DocSentinel/issues/new?template=new_skill_template.md) 提交或添加到 `examples/templates/`。

### 分支与发布

-   主开发分支为 **`main`**。
-   发版通过 **Git tag**（如 `v4.0.0`）与 [GitHub Releases](https://github.com/arthurpanhku/DocSentinel/releases) 完成；版本说明见 [CHANGELOG.md](CHANGELOG.md)。
