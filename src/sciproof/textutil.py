"""Make untrusted strings safe to print on a terminal."""

from __future__ import annotations


def safe_text(value: object, limit: int = 500) -> str:
    """Escape control characters (including ANSI escape sequences) and shorten long strings."""
    text = value if isinstance(value, str) else repr(value)
    out = []
    for char in text:
        code = ord(char)
        if char == "\n":
            out.append("\\n")
        elif code < 32 or code == 127 or 0x80 <= code < 0xA0:
            out.append(f"\\x{code:02x}")
        else:
            out.append(char)
    result = "".join(out)
    if len(result) > limit:
        result = result[:limit] + f"... [{len(result) - limit} more characters]"
    return result
