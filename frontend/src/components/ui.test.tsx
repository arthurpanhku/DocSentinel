import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RefreshCw } from "lucide-react";
import { describe, expect, it, vi } from "vitest";

import { IconButton } from "./ui";

describe("IconButton", () => {
  it("exposes an accessible name and handles clicks", async () => {
    const onClick = vi.fn();
    render(
      <TooltipPrimitive.Provider>
        <IconButton label="Refresh assessments" onClick={onClick}>
          <RefreshCw aria-hidden="true" />
        </IconButton>
      </TooltipPrimitive.Provider>
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Refresh assessments" })
    );
    expect(onClick).toHaveBeenCalledOnce();
  });
});
