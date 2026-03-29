import logging
import re

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
