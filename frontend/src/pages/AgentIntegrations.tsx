import { useQuery } from "@tanstack/react-query";
import {
  Bot,
  Braces,
  Check,
  Copy,
  KeyRound,
  Network,
  RefreshCw,
  ShieldCheck
} from "lucide-react";
import { useState } from "react";

import {
  Badge,
  Card,
  CardHeader,
  ErrorNote,
  IconButton,
  PageHeader
} from "../components/ui";
import { getAgentIntegrationStatus } from "../lib/api";

const accessLabels = {
  loopback_only: "Loopback only",
  bearer_token: "Bearer token",
  disabled: "Disabled"
} as const;

function CapabilityList({
  title,
  items
}: {
  title: string;
  items: string[];
}) {
  return (
    <Card>
      <CardHeader title={title} meta={`${items.length} exposed capabilities`} />
      <div className="divide-y divide-line">
        {items.map((item) => (
          <div key={item} className="flex min-h-11 items-center gap-3 px-4 py-2">
            <Braces className="h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
            <code className="min-w-0 break-all text-xs text-text">{item}</code>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function AgentIntegrations() {
  const [copied, setCopied] = useState<string | null>(null);
  const status = useQuery({
    queryKey: ["agent-integrations"],
    queryFn: getAgentIntegrationStatus
  });

  async function copyEndpoint(endpoint: string) {
    await navigator.clipboard.writeText(`${window.location.origin}${endpoint}`);
    setCopied(endpoint);
    window.setTimeout(() => setCopied(null), 1600);
  }

  const data = status.data;
  return (
    <div className="space-y-5">
      <PageHeader
        title="Agent Integrations"
        description="Protocol endpoints and capabilities exposed to approved agent runtimes."
        actions={
          <>
            <Badge tone={data?.enabled ? "good" : "bad"}>
              {data?.enabled ? "Gateway enabled" : "Gateway disabled"}
            </Badge>
            <IconButton
              label="Refresh agent integrations"
              onClick={() => void status.refetch()}
              disabled={status.isFetching}
            >
              <RefreshCw aria-hidden="true" />
            </IconButton>
          </>
        }
      />

      <ErrorNote
        message={status.error instanceof Error ? status.error.message : null}
      />

      {data ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader title="Access" />
              <div className="flex min-h-28 items-center gap-4 p-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-md border border-line bg-panel2 text-accent">
                  <KeyRound className="h-4 w-4" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-text">
                    {accessLabels[data.access_mode]}
                  </div>
                  <div className="mt-1 text-xs text-muted">
                    Runtime-managed credentials
                  </div>
                </div>
              </div>
            </Card>
            <Card>
              <CardHeader title="Document boundary" />
              <div className="flex min-h-28 items-center gap-4 p-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-md border border-line bg-panel2 text-good">
                  <ShieldCheck className="h-4 w-4" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-text">
                    {data.document_roots_configured} approved root
                    {data.document_roots_configured === 1 ? "" : "s"}
                  </div>
                  <div className="mt-1 text-xs text-muted">
                    Path and symlink confinement
                  </div>
                </div>
              </div>
            </Card>
            <Card>
              <CardHeader title="Review policy" />
              <div className="flex min-h-28 items-center gap-4 p-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-md border border-line bg-panel2 text-warn">
                  <Bot className="h-4 w-4" aria-hidden="true" />
                </div>
                <div>
                  <div className="text-sm font-medium text-text">
                    Human approval required
                  </div>
                  <div className="mt-1 text-xs text-muted">
                    Agent output remains a draft
                  </div>
                </div>
              </div>
            </Card>
          </div>

          <Card>
            <CardHeader
              title="Protocol endpoints"
              meta="Local endpoints are shown using the current console origin."
              action={<Network className="h-4 w-4 text-accent" aria-hidden="true" />}
            />
            <div className="divide-y divide-line">
              {data.protocols.map((protocol) => (
                <div
                  key={protocol.protocol}
                  className="grid gap-3 px-4 py-4 sm:grid-cols-[120px_1fr_auto] sm:items-center"
                >
                  <div className="flex items-center gap-2">
                    <Badge tone={protocol.enabled ? "good" : "bad"}>
                      {protocol.protocol.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-muted">{protocol.transport}</span>
                  </div>
                  <code className="min-w-0 break-all text-xs text-text">
                    {window.location.origin}
                    {protocol.endpoint}
                  </code>
                  <IconButton
                    label={`Copy ${protocol.protocol.toUpperCase()} endpoint`}
                    onClick={() => void copyEndpoint(protocol.endpoint)}
                  >
                    {copied === protocol.endpoint ? (
                      <Check aria-hidden="true" />
                    ) : (
                      <Copy aria-hidden="true" />
                    )}
                  </IconButton>
                </div>
              ))}
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <CapabilityList title="MCP Tools" items={data.mcp_tools} />
            <CapabilityList title="A2A Skills" items={data.a2a_skills} />
          </div>

          <div className="border-l-2 border-accent px-4 py-2 text-sm text-muted">
            {data.data_boundary}
          </div>
        </>
      ) : null}
    </div>
  );
}
