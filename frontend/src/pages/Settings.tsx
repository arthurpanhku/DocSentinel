import { KeyRound, RefreshCw, Save, Server, Terminal } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  Badge,
  Button,
  Card,
  CardHeader,
  ErrorNote,
  Field,
  IconButton,
  Input,
  PageHeader,
  Select
} from "../components/ui";
import { getHealth, getLLMConfig, updateLLMConfig } from "../lib/api";
import type { LLMConfig } from "../types";

export default function Settings() {
  const [health, setHealth] = useState<string>("checking");
  const [llm, setLlm] = useState<LLMConfig | null>(null);
  const [apiBase, setApiBase] = useState(window.location.origin);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");

  async function load() {
    setError(null);
    setMessage(null);
    try {
      const [healthResult, llmResult] = await Promise.all([
        getHealth().catch(() => ({ status: "down" })),
        getLLMConfig().catch(() => null)
      ]);
      setHealth(healthResult.status);
      setLlm(llmResult);
      if (llmResult) {
        setProvider(llmResult.provider);
        setModel(llmResult.model || "");
        setBaseUrl(llmResult.base_url || "");
        setApiKey("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load settings.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const selectedProvider = useMemo(
    () => llm?.providers?.find((item) => item.id === provider),
    [llm?.providers, provider]
  );

  function handleProviderChange(nextProvider: string) {
    setProvider(nextProvider);
    const preset = llm?.providers?.find((item) => item.id === nextProvider);
    if (preset) {
      setModel(preset.default_model);
      setBaseUrl(preset.default_base_url);
      setApiKey("");
    }
  }

  async function handleLLMSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await updateLLMConfig({
        provider,
        model,
        base_url: baseUrl,
        api_key: apiKey || undefined
      });
      if (result.status === "error") {
        setError(result.message || "Unable to update LLM config.");
      } else {
        setMessage("LLM configuration updated for this running server.");
        setLlm((current) => ({
          ...(current || {}),
          ...result,
          providers: current?.providers || llm?.providers
        }));
        setApiKey("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update LLM config.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Settings"
        description="Runtime health, model configuration, and local data boundaries."
        actions={
          <IconButton label="Refresh settings" onClick={() => void load()}>
            <RefreshCw aria-hidden="true" />
          </IconButton>
        }
      />
      <ErrorNote message={error} />
      {message ? <div className="rounded-md border border-good/30 bg-good/10 px-3 py-2 text-sm text-good">{message}</div> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="System" action={<Server className="h-4 w-4 text-accent" />} />
          <div className="space-y-4 p-4">
            <div className="flex items-center justify-between gap-3 rounded-md border border-line bg-panel2 p-3">
              <div>
                <div className="text-sm font-medium text-text">API health</div>
                <div className="mt-1 text-xs text-muted">GET /health</div>
              </div>
              <Badge tone={health === "ok" ? "good" : "bad"}>{health}</Badge>
            </div>
            <div className="flex items-center justify-between gap-3 rounded-md border border-line bg-panel2 p-3">
              <div>
                <div className="text-sm font-medium text-text">LLM provider</div>
                <div className="mt-1 text-xs text-muted">GET /config/llm</div>
              </div>
              <Badge tone="accent">{llm ? `${llm.provider}: ${llm.model}` : "unknown"}</Badge>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="LLM Configuration" action={<KeyRound className="h-4 w-4 text-accent" />} />
          <form onSubmit={handleLLMSave} className="space-y-4 p-4">
            <div className="grid gap-3 md:grid-cols-2">
              <Field label="Provider">
                <Select value={provider} onChange={(event) => handleProviderChange(event.target.value)}>
                  {(llm?.providers || []).map((item) => (
                    <option key={item.id} value={item.id}>{item.label}</option>
                  ))}
                  {!llm?.providers?.length ? <option value="ollama">Ollama</option> : null}
                </Select>
              </Field>
              <Field label="Model">
                <Input value={model} onChange={(event) => setModel(event.target.value)} placeholder="gpt-4o-mini" />
              </Field>
            </div>
            <Field label="Base URL">
              <Input
                value={baseUrl}
                onChange={(event) => setBaseUrl(event.target.value)}
                placeholder={selectedProvider?.default_base_url || "https://api.openai.com/v1"}
              />
            </Field>
            <Field label={selectedProvider?.requires_api_key ? "API Key" : "API Key (optional for local providers)"}>
              <Input
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                type="password"
                placeholder={llm?.api_key_preview ? `Current: ${llm.api_key_preview}` : "Paste key to update"}
              />
            </Field>
            <div className="rounded-md border border-line bg-panel2 p-3 text-sm leading-6 text-muted">
              Keys are accepted by the local FastAPI process and returned only as a masked preview. Restarting the server reloads values from `.env`.
            </div>
            <Button disabled={busy}>
              <Save className="h-4 w-4" />
              Save LLM config
            </Button>
          </form>
        </Card>

        <Card>
          <CardHeader title="Console Runtime" action={<Terminal className="h-4 w-4 text-accent" />} />
          <div className="space-y-4 p-4">
            <Field label="API base URL">
              <Input value={apiBase} onChange={(event) => setApiBase(event.target.value)} />
            </Field>
            <div className="rounded-md border border-line bg-panel2 p-3 text-sm leading-6 text-muted">
              Production console calls the same FastAPI origin. During development, Vite proxies /api, /health, and /config to localhost:8000.
            </div>
            <div className="grid gap-2 rounded-md border border-line bg-[#0d1117] p-3 font-mono text-xs text-muted">
              <span>npm install --prefix frontend</span>
              <span>npm run build --prefix frontend</span>
              <span>uvicorn app.main:app --reload --host 0.0.0.0 --port 8000</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
