# Agent Integration Guide | 代理集成指南

DocSentinel supports the **Model Context Protocol (MCP)**, allowing it to be used as a "skill" or "tool" by other autonomous agents (like Claude Desktop, OpenClaw, or LangChain agents).

DocSentinel 支持 **Model Context Protocol (MCP)**，使其能够作为“技能”或“工具”被其他自主智能体（如 Claude Desktop、OpenClaw 或 LangChain Agent）调用。

---

## 🔌 Model Context Protocol (MCP)

DocSentinel exposes its core capabilities (document assessment and knowledge base retrieval) as an MCP Server.

DocSentinel 将其核心能力（文档评估和知识库检索）作为 MCP Server 对外暴露。

### Available Tools | 可用工具

| Tool Name              | Description (English)                                              | 说明 (Chinese)                           | Inputs                                           |
| :--------------------- | :----------------------------------------------------------------- | :--------------------------------------- | :----------------------------------------------- |
| `assess_document`      | Analyze a security document (PDF/Word) and generate a risk report. Supports SSDLC stage selection. | 分析安全文档并生成风险报告。支持 SSDLC 阶段选择。 | `file_path` (str), `scenario_id` (str, optional), `ssdlc_stage` (str, optional) |
| `query_knowledge_base` | Search the internal security policy database.                      | 检索内部安全策略数据库。                 | `query` (str), `top_k` (int, optional)           |

### 🚀 How to Use with Claude Desktop | 在 Claude Desktop 中使用

1.  **Install DocSentinel**:
    **安装 DocSentinel**：
    ```bash
    pip install docsentinel
    # or install from source
    # 或从源码安装
    pip install -e .
    ```

2.  **Configure Claude Desktop**:
    Edit your `claude_desktop_config.json` (usually in `~/Library/Application Support/Claude/` on macOS):

    **配置 Claude Desktop**：
    编辑 `claude_desktop_config.json`（macOS 上通常位于 `~/Library/Application Support/Claude/`）：

    ```json
    {
      "mcpServers": {
        "docsentinel-security": {
          "command": "docsentinel-mcp",
          "args": [],
          "env": {
            "OPENAI_API_KEY": "sk-...",
            "CHROMA_PERSIST_DIR": "/absolute/path/to/data/chroma"
          }
        }
      }
    }
    ```

3.  **Restart Claude Desktop**. You can now ask Claude:
    > "Check the security design document at `/Users/me/docs/design.pdf` for compliance risks using DocSentinel at the Design stage."
    >
    > "Assess this SAST report against our testing standards — use the Testing SSDLC stage."

    **重启 Claude Desktop**。现在你可以问 Claude：
    > "使用 DocSentinel 的设计阶段检查 `/Users/me/docs/design.pdf` 的安全合规风险。"
    >
    > "评估这份 SAST 报告——使用测试阶段的 SSDLC 技能。"

### 🤖 How to Use with OpenClaw / LangChain | 在 OpenClaw / LangChain 中使用

Since DocSentinel implements the standard MCP protocol, any MCP-compliant client can connect to it.

由于 DocSentinel 实现了标准的 MCP 协议，任何兼容 MCP 的客户端均可连接。

**Example (Python Client):**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="docsentinel-mcp",
    args=[],
    env={"OPENAI_API_KEY": "sk-..."}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # List tools
        tools = await session.list_tools()
        
        # Call assessment tool
        result = await session.call_tool(
            "assess_document",
            arguments={"file_path": "/path/to/doc.pdf"}
        )
        print(result.content)
```

---

## 🤝 OpenClaw Integration | OpenClaw 集成

(Coming Soon: Direct integration guide via OpenClaw's standardized agent interface registry.)

（即将推出：通过 OpenClaw 标准化代理接口注册表的直接集成指南。）
