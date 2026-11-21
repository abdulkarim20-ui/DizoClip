"""Display-only masking for secrets. Nothing in this module is ever written to disk."""
from __future__ import annotations

MASK_CHAR = "*"
MASK_WIDTH = 20  # fixed star run so the real length is not revealed


def mask_secret(secret: str) -> str:
    n = len(secret or "")
    if n == 0:
        return ""
    if n >= 20:
        edge = 3
    elif n >= 12:
        edge = 2
    else:
        edge = 0  # short secrets are fully hidden
    if edge == 0:
        return MASK_CHAR * MASK_WIDTH
    return f"{secret[:edge]}{MASK_CHAR * MASK_WIDTH}{secret[-edge:]}"


def looks_masked(value: str) -> bool:
    """True if `value` looks like a display mask (or the old stored mask), not a real secret."""
    if not value:
        return False
    return any(ch * 8 in value for ch in ("*", "•"))
