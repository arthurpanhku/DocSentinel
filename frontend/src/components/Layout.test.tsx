import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "../app/providers";
import Layout from "./Layout";

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <AppProviders>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<h1>Workspace content</h1>} />
            <Route path="integrations" element={<h1>Gateway content</h1>} />
          </Route>
        </Routes>
      </AppProviders>
    </MemoryRouter>
  );
}

describe("Layout", () => {
  beforeEach(() => {
    const values = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      clear: () => values.clear(),
      getItem: (key: string) => values.get(key) ?? null,
      key: (index: number) => [...values.keys()][index] ?? null,
      length: 0,
      removeItem: (key: string) => values.delete(key),
      setItem: (key: string, value: string) => values.set(key, value)
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("groups navigation by user workflow", () => {
    renderLayout();

    expect(screen.getByText("Review & govern")).toBeInTheDocument();
    expect(screen.getByText("Agent operations")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Assessment queue" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Agent gateway" })
    ).toBeInTheDocument();
  });

  it("opens the command palette with the standard keyboard shortcut", async () => {
    const user = userEvent.setup();
    renderLayout();

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const dialog = screen.getByRole("dialog", { name: "Search navigation" });
    expect(dialog).toBeInTheDocument();

    await user.type(
      screen.getByRole("textbox", { name: "Search navigation" }),
      "mcp"
    );
    expect(
      screen.getByRole("button", { name: /Agent gateway.*Agent operations/ })
    ).toBeInTheDocument();
  });
});
