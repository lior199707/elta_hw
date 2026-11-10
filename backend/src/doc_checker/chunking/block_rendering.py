from __future__ import annotations

import math

from doc_checker.constants import CHARS_PER_TOKEN_ESTIMATE, HEADING_PATH_SEPARATOR
from doc_checker.custom_types.document_types import Block


def render_block_line(block: Block) -> str:
    """Render a block the way the model sees it: `[B12] (1 Specs > 1.2 Radar) text`."""
    if not block.heading_path:
        return f"[{block.block_id}] {block.text}"
    return f"[{block.block_id}] ({HEADING_PATH_SEPARATOR.join(block.heading_path)}) {block.text}"


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (characters / 4, rounded up). Only needs to be roughly right."""
    return math.ceil(len(text) / CHARS_PER_TOKEN_ESTIMATE)
