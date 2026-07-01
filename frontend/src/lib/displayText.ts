const cjkPattern = /[\p{Script=Han}\u3000-\u303f\uff00-\uffef]/u;
const cjkParentheticalPattern = /\s*[\(\[][^)\]]*[\p{Script=Han}][^)\]]*[\)\]]/gu;
const cjkRunPattern = /[\p{Script=Han}]+/gu;

const frameworkLabels: Record<string, string> = {
  "china-mlps2": "China Multi-Level Protection Scheme 2.0"
};

export function frameworkDisplayName(
  frameworkId: string,
  value?: string | null
) {
  return frameworkLabels[frameworkId] ?? englishDisplayText(value, frameworkId);
}

export function englishDisplayText(value?: string | null, fallback = "") {
  if (!value) return fallback;
  if (!cjkPattern.test(value)) return value;

  const cleaned = value
    .replace(cjkParentheticalPattern, "")
    .replace(cjkRunPattern, "")
    .replace(/\s+([,.;:])/g, "$1")
    .replace(/[-\u2013\u2014:\uff1a\uff1b;,\s]+$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();

  return cleaned || fallback;
}

export function hasLocalizedText(value?: string | null) {
  return Boolean(value && cjkPattern.test(value));
}
