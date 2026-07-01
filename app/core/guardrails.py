import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass

from fastapi import HTTPException

logger = logging.getLogger(__name__)

INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?prior\s+(instructions|context)",
        r"override\s+system\s+prompt",
        r"reveal\s+(your\s+)?system\s+prompt",
        r"print\s+(your\s+)?system\s+prompt",
        r"output\s+(your\s+)?(initial|system)\s+instructions",
        r"jailbreak",
        r"DAN\s+mode",
        r"admin\s+access",
        r"drop\s+table",
        r"<\s*script[\s>]",
    ]
]

MAX_INPUT_LENGTH = 500_000

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}" r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
_CN_MOBILE_RE = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d{9}(?!\d)")
_HOST_RE = re.compile(
    r"\b(?:[A-Za-z0-9-]+\.)+(?:corp|internal|local|example|com|net|org)\b"
)


@dataclass(frozen=True)
class SanitizedText:
    text: str
    redacted_fields: list[str]


def sanitize_input(text: str) -> str:
    """Check text for prompt injection patterns. Raises on detection.

    Returns the original text unmodified when no injection is detected,
    so callers can safely chain: ``clean = sanitize_input(raw)``.
    """
    if not text:
        return text

    if len(text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Input exceeds maximum allowed length ({MAX_INPUT_LENGTH} chars).",
        )

    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.warning(
                "Prompt injection attempt detected: matched pattern=%s, snippet=%r",
                pattern.pattern,
                text[max(0, match.start() - 20) : match.end() + 20],
            )
            raise HTTPException(
                status_code=400,
                detail="Input rejected: potentially unsafe content detected.",
            )

    return text


def sanitize_text(text: str | None) -> SanitizedText:
    """Redact common PII and infrastructure markers before LLM use."""
    value = text or ""
    redacted: list[str] = []
    replacements = [
        ("email", _EMAIL_RE, "[REDACTED_EMAIL]"),
        ("ipv4", _IPV4_RE, "[REDACTED_IP]"),
        ("cn_mobile", _CN_MOBILE_RE, "[REDACTED_PHONE]"),
        ("hostname", _HOST_RE, "[REDACTED_HOST]"),
    ]
    for label, pattern, marker in replacements:
        value, count = pattern.subn(marker, value)
        if count:
            redacted.append(label)
    return SanitizedText(value, sorted(set(redacted)))


def merge_redactions(*items: Iterable[str]) -> list[str]:
    merged: set[str] = set()
    for item in items:
        merged.update(item)
    return sorted(merged)
