import { LogIn, ShieldCheck } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button, Card, ErrorNote, Field, Input } from "../components/ui";
import { login, saveGovernanceSession } from "../lib/governanceApi";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const session = await login(email, password);
      saveGovernanceSession(session);
      navigate("/governance");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 py-10">
      <Card className="w-full max-w-md p-5">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-accent/35 bg-accent/10 text-accent">
            <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-text">Governance sign in</h1>
            <p className="text-sm text-muted">JWT session for portal workflows</p>
          </div>
        </div>

        <form className="grid gap-4" onSubmit={(event) => void onSubmit(event)}>
          <Field label="Email or username">
            <Input
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Field>
          <Field label="Password">
            <Input
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>
          <ErrorNote message={error} />
          <div className="flex items-center justify-between gap-3">
            <Link className="text-sm text-muted hover:text-text" to="/">
              Back to console
            </Link>
            <Button disabled={loading || !email || !password} type="submit">
              <LogIn className="h-4 w-4" aria-hidden="true" />
              {loading ? "Signing in" : "Sign in"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
