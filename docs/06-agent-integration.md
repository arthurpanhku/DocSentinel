# Agent Integration Guide | Agent 集成指南

DocSentinel supports complementary interoperability protocols:

- **MCP** exposes narrow tools to coding agents and workflow platforms.
- **A2A 1.0** exposes DocSentinel as a remote security-assessment agent.

Both protocols use the same assessment task service as the REST API and React
console. Agent submissions always require human review.

## Security Model | 安全模型

- Document paths must resolve inside `MCP_DOCUMENT_ROOTS`.
- With an empty `AGENT_GATEWAY_TOKEN`, remote protocol endpoints accept
  loopback clients only.
- Network exposure requires a bearer token, TLS, and preferably an upstream
  OIDC-aware proxy.
- Protocol adapters do not return raw source documents. Assessment content may
  still be sent to the configured LLM provider, so local/private LLM policy
  remains important.
- Agents can submit and inspect assessments, but cannot approve their own work.

## MCP

### Tools

| Tool | Purpose |
| :--- | :--- |
| `submit_document_assessment` | Submit a document asynchronously; returns the shared assessment task ID. |
| `get_assessment_status` | Read task status and the available draft report. |
| `query_knowledge_base` | Retrieve approved KB chunks, limited to 10 results. |
| `get_agent_gateway_status` | Inspect enabled protocols and access mode. |
| `assess_document` | Compatibility tool that waits for a draft assessment. |

### Local stdio

Use stdio for Claude Desktop, Cursor, and other agents running on the same
machine:

```json
{
  "mcpServers": {
    "docsentinel": {
      "command": "/path/to/DocSentinel/.venv/bin/python",
      "args": ["/path/to/DocSentinel/app/mcp_server.py"],
      "env": {
        "MCP_DOCUMENT_ROOTS": "/absolute/path/to/approved/documents",
        "LLM_PROVIDER": "ollama"
      }
    }
  }
}
```

Use `:` to separate multiple roots on macOS/Linux, or `;` on Windows.

### Streamable HTTP

When FastAPI is running, the MCP endpoint is:

```text
http://localhost:8000/mcp/
```

For access from another host:

```dotenv
AGENT_GATEWAY_TOKEN=generate-a-long-random-value
AGENT_GATEWAY_PUBLIC_URL=https://docsentinel.internal.example
AGENT_GATEWAY_ALLOWED_HOSTS=docsentinel.internal.example
AGENT_GATEWAY_ALLOWED_ORIGINS=https://trusted-agent-console.internal.example
```

Clients must send:

```http
Authorization: Bearer <AGENT_GATEWAY_TOKEN>
```

Use the MCP Inspector or a conforming client to initialize the connection and
discover tools. The endpoint is not a conventional REST API. Keep the Host and
Origin allow-lists narrow: they are part of MCP's DNS-rebinding protection and
must match the deployment URL used by clients.

Docker bridge traffic is not loopback traffic from the container's perspective.
Set `AGENT_GATEWAY_TOKEN` when connecting to MCP or A2A through a published
container port.

## A2A 1.0

Agent discovery:

```text
http://localhost:8000/.well-known/agent-card.json
```

JSON-RPC endpoint:

```text
http://localhost:8000/a2a
```

The Agent Card advertises three skills:

- `assess_security_document`
- `get_security_assessment`
- `query_security_knowledge`

A2A message text must contain a JSON object.

Submit an approved server-side document:

```json
{
  "operation": "assess_document",
  "file_path": "./examples/security-design.md",
  "phase": "design",
  "scenario_id": "architecture-review",
  "skill_id": "ssdlc-design"
}
```

Retrieve the shared task:

```json
{
  "operation": "get_assessment",
  "task_id": "assessment-task-id"
}
```

Query security knowledge:

```json
{
  "operation": "query_knowledge_base",
  "query": "PCI DSS privileged access requirements",
  "top_k": 3
}
```

This first A2A slice references documents already present in an approved
server-side root. Cross-host uploads will use opaque document handles in a
future phase rather than granting agents broader filesystem access.

## Operations

The React console exposes protocol state at:

```text
http://localhost:8000/console/integrations
```

The machine-readable status endpoint is:

```text
GET /api/v1/integrations/agents/status
```

Use logs and assessment activity records to trace which entry point created a
task (`rest`, `mcp`, or `a2a`).
