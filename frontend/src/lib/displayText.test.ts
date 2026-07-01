import { describe, expect, it } from "vitest";

import {
  englishDisplayText,
  frameworkDisplayName,
  hasLocalizedText
} from "./displayText";

const localizedIdentity = String.fromCharCode(0x8eab, 0x4efd, 0x9274, 0x5225);
const localizedAudit = String.fromCharCode(0x5b89, 0x5168, 0x5ba1, 0x8ba1);

describe("display text normalization", () => {
  it("uses English framework fallbacks for known localized overlays", () => {
    expect(
      frameworkDisplayName(
        "china-mlps2",
        "China Multi-Level Protection Scheme 2.0 (dengbao)"
      )
    ).toBe("China Multi-Level Protection Scheme 2.0");
  });

  it("removes localized suffixes from mixed framework citations", () => {
    expect(englishDisplayText("GB/T 22239-2019 §7.1.4.1 -- identity")).toBe(
      "GB/T 22239-2019 §7.1.4.1 -- identity"
    );
    expect(
      englishDisplayText(`GB/T 22239-2019 §7.1.4.1 -- ${localizedIdentity}`)
    ).toBe("GB/T 22239-2019 §7.1.4.1");
  });

  it("detects localized text", () => {
    expect(hasLocalizedText("Security audit")).toBe(false);
    expect(hasLocalizedText(localizedAudit)).toBe(true);
  });
});
