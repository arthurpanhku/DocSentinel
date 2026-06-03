import { Database, FolderSync, Search, Upload } from "lucide-react";
import { FormEvent, useState } from "react";

import { Badge, Button, Card, CardHeader, EmptyState, ErrorNote, Field, Input, Textarea } from "../components/ui";
import { queryKb, reindexKb, uploadKbDocument } from "../lib/api";
import type { KBChunk } from "../types";

export default function KnowledgeBase() {
  const [chunks, setChunks] = useState<KBChunk[]>([]);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [reindexResult, setReindexResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || !file.size) {
      setError("Select a knowledge base document.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await uploadKbDocument(file);
      setUploadResult(result.document_id);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const query = String(form.get("query") || "").trim();
    const topK = Number(form.get("top_k") || 5);
    if (!query) return;
    setBusy(true);
    setError(null);
    try {
      const result = await queryKb(query, topK);
      setChunks(result.chunks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReindex(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const directory = String(form.get("directory") || "").trim();
    if (!directory) return;
    setBusy(true);
    setError(null);
    try {
      const result = await reindexKb(directory);
      setReindexResult(JSON.stringify(result));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reindex failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-text">Knowledge Base</h1>
        <p className="mt-1 text-sm text-muted">Upload security references, query RAG context, and reindex local folders.</p>
      </div>
      <ErrorNote message={error} />

      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader title="Upload Document" meta="Ingest into vector and graph retrieval." />
            <form onSubmit={handleUpload} className="space-y-3 p-4">
              <Field label="Document">
                <Input name="file" type="file" accept=".txt,.md,.pdf,.docx,.xlsx,.pptx" />
              </Field>
              <Button disabled={busy} className="w-full">
                <Upload className="h-4 w-4" />
                Upload
              </Button>
              {uploadResult ? <Badge tone="good">document {uploadResult}</Badge> : null}
            </form>
          </Card>

          <Card>
            <CardHeader title="Reindex Directory" meta="Server-side directory path." />
            <form onSubmit={handleReindex} className="space-y-3 p-4">
              <Field label="Directory">
                <Input name="directory" defaultValue="./examples" />
              </Field>
              <Button disabled={busy} variant="quiet" className="w-full">
                <FolderSync className="h-4 w-4" />
                Reindex
              </Button>
              {reindexResult ? <pre className="overflow-auto rounded-md border border-line bg-panel2 p-2 text-xs text-muted">{reindexResult}</pre> : null}
            </form>
          </Card>
        </div>

        <Card>
          <CardHeader title="RAG Query" action={<Database className="h-4 w-4 text-accent" />} />
          <form onSubmit={handleQuery} className="grid gap-3 border-b border-line p-4 md:grid-cols-[1fr_100px_auto]">
            <Field label="Query">
              <Textarea name="query" placeholder="What access control evidence is required?" className="min-h-20" />
            </Field>
            <Field label="Top K">
              <Input name="top_k" type="number" min={1} max={20} defaultValue={5} />
            </Field>
            <div className="flex items-end">
              <Button disabled={busy} className="w-full">
                <Search className="h-4 w-4" />
                Query
              </Button>
            </div>
          </form>
          {chunks.length ? (
            <div className="grid gap-3 p-4">
              {chunks.map((chunk, index) => (
                <div key={index} className="rounded-md border border-line bg-panel2 p-3">
                  <div className="mb-2 flex flex-wrap gap-2">
                    <Badge tone="accent">chunk {index + 1}</Badge>
                    {Object.entries(chunk.metadata).slice(0, 4).map(([key, value]) => (
                      <Badge key={key}>{key}: {String(value)}</Badge>
                    ))}
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-6 text-text">{chunk.content}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Run a query to inspect retrieved context." />
          )}
        </Card>
      </div>
    </div>
  );
}
