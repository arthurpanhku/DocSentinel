# Agent Integration Guide | 代理集成指南

Arthor-Agent supports the **Model Context Protocol (MCP)**, allowing it to be used as a "skill" or "tool" by other autonomous agents (like Claude Desktop, OpenClaw, or LangChain agents).

---

## 🔌 Model Context Protocol (MCP)

Arthor-Agent exposes its core capabilities (document assessment and knowledge base retrieval) as an MCP Server.

### Available Tools

| Tool Name | Description | Inputs |
| :--- | :--- | :--- |
| `assess_document` | Analyze a security document (PDF/Word) and generate a risk report. | `file_path` (str), `scenario_id` (str, optional) |
| `query_knowledge_base` | Search the internal security policy database. | `query` (str), `top_k` (int, optional) |

### 🚀 How to Use with Claude Desktop

1.  **Install Arthor-Agent**:
    ```bash
    pip install arthor-agent
    # or install from source
    pip install -e .
    ```

2.  **Configure Claude Desktop**:
    Edit your `claude_desktop_config.json` (usually in `~/Library/Application Support/Claude/` on macOS):

    ```json
    {
      "mcpServers": {
        "arthor-security": {
          "command": "arthor-mcp",
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
    > "Check the security design document at `/Users/me/docs/design.pdf` for compliance risks using Arthor."

### 🤖 How to Use with OpenClaw / LangChain

Since Arthor-Agent implements the standard MCP protocol, any MCP-compliant client can connect to it.

**Example (Python Client):**

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="arthor-mcp",
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

## 🤝 OpenClaw Integration

(Coming Soon: Direct integration guide via OpenClaw's standardized agent interface registry.)
