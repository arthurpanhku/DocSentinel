import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "../app/providers";
import AgentIntegrations from "./AgentIntegrations";

describe("AgentIntegrations", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            enabled: true,
            access_mode: "loopback_only",
            protocols: [
              {
                protocol: "mcp",
                transport: "streamable-http",
                endpoint: "/mcp/",
                enabled: true
              },
              {
                protocol: "a2a",
                transport: "json-rpc",
                endpoint: "/a2a",
                enabled: true
              }
            ],
            mcp_tools: ["submit_document_assessment"],
            a2a_skills: ["assess_security_document"],
            document_roots_configured: 1,
            data_boundary: "Agent protocols do not return raw documents."
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows protocol endpoints and access policy", async () => {
    render(
      <MemoryRouter>
        <AppProviders>
          <AgentIntegrations />
        </AppProviders>
      </MemoryRouter>
    );

    expect(
      await screen.findByRole("heading", { name: "Agent Integrations" })
    ).toBeInTheDocument();
    expect(await screen.findByText("Loopback only")).toBeInTheDocument();
    expect(await screen.findByText("MCP")).toBeInTheDocument();
    expect(await screen.findByText("A2A")).toBeInTheDocument();
    expect(
      await screen.findByText("submit_document_assessment")
    ).toBeInTheDocument();
  });
});
