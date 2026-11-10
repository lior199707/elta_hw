from __future__ import annotations

from doc_checker.constants import QUOTE_CHAR_EQUIVALENTS, QUOTE_WRAPPER_CHARS
from doc_checker.extraction.text_normalization import normalize_whitespace

_EQUIVALENCE_TABLE = str.maketrans(QUOTE_CHAR_EQUIVALENTS)


def clean_quote(quote: str) -> str:
    """Normalize whitespace and strip wrapping quote marks the model may add."""
    return normalize_whitespace(quote).strip(QUOTE_WRAPPER_CHARS)


def find_quote(text: str, quote: str) -> tuple[int, int] | None:
    """Return (start, end) of the first occurrence of `quote` in `text`, or None.

    Tolerates differences in whitespace, curly vs straight quotes, dash variants and case.
    Offsets index into `text` itself, so `text[start:end]` is the exact document wording.
    """
    haystack = _canonical(text)
    # Try the quote as given first: its quote marks may be part of the document wording.
    for variant in (normalize_whitespace(quote), clean_quote(quote)):
        if not variant:
            continue
        needle = _canonical(variant)
        position = haystack.find(needle)
        if position >= 0:
            return position, position + len(needle)
    return None


def _canonical(text: str) -> str:
    """Length-preserving canonical form, so offsets map back to the original text."""
    translated = text.translate(_EQUIVALENCE_TABLE)
    lowered = translated.lower()
    return lowered if len(lowered) == len(translated) else translated
