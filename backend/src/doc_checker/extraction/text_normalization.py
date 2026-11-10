from __future__ import annotations


def normalize_whitespace(text: str) -> str:
    """Collapse every run of Unicode whitespace (tabs, newlines, NBSP) into one space."""
    return " ".join(text.split())
