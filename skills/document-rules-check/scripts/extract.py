# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.2"]
# ///
"""Validate a .docx/.txt file, extract numbered blocks and write chunk files.

Usage: uv run scripts/extract.py <document> [--workspace DIR] [--chunk-tokens 8000] [--overlap 2]
Prints one JSON object. Exit codes: 0 ok, 1 bad arguments, 2 unsupported type,
3 not found / unreadable, 4 empty, 5 too large.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_rules_lib import (  # noqa: E402
    BLOCKS_FILE,
    CHUNKS_DIR,
    FINDINGS_DIR,
    REPORT_JSON,
    REPORT_MD,
    SkillError,
    build_chunks,
    chunk_id,
    extract_blocks,
    render_line,
)

DEFAULT_CHUNK_TOKENS = 8000
DEFAULT_OVERLAP = 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--chunk-tokens", type=int, default=DEFAULT_CHUNK_TOKENS)
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP)
    args = parser.parse_args()

    document: Path = args.document.resolve()
    workspace: Path = args.workspace or document.with_name(f"{document.stem}.rules-check")
    try:
        blocks = extract_blocks(document)
        chunks = build_chunks(blocks, args.chunk_tokens, args.overlap)
    except SkillError as exc:
        print(json.dumps({"ok": False, "code": exc.code, "error": str(exc)}))
        return exc.exit_code

    workspace = workspace.resolve()
    # A fresh extraction invalidates old chunks, findings and reports; rules.json is kept.
    for stale in (CHUNKS_DIR, FINDINGS_DIR):
        shutil.rmtree(workspace / stale, ignore_errors=True)
    for stale in (REPORT_MD, REPORT_JSON):
        (workspace / stale).unlink(missing_ok=True)
    (workspace / CHUNKS_DIR).mkdir(parents=True)
    (workspace / FINDINGS_DIR).mkdir()

    chunk_index = []
    for number, chunk in enumerate(chunks, start=1):
        name = chunk_id(number)
        header = (
            f"# {name} of {len(chunks)}: blocks {chunk[0].block_id} to {chunk[-1].block_id} "
            f"of {len(blocks)}\n"
        )
        body = "\n".join(render_line(block) for block in chunk)
        (workspace / CHUNKS_DIR / f"{name}.txt").write_text(header + body + "\n", encoding="utf-8")
        chunk_index.append(
            {"chunk": name, "first_block": chunk[0].block_id, "last_block": chunk[-1].block_id}
        )

    meta = {
        "document": document.name,
        "document_path": str(document),
        "block_count": len(blocks),
        "chunk_count": len(chunks),
        "has_page_layout": any(block.page is not None for block in blocks),
        "chunks": chunk_index,
        "blocks": [asdict(block) for block in blocks],
    }
    (workspace / BLOCKS_FILE).write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "workspace": str(workspace),
                "document": document.name,
                "block_count": len(blocks),
                "chunk_count": len(chunks),
                "has_page_layout": meta["has_page_layout"],
                "chunks": [f"{CHUNKS_DIR}/{c['chunk']}.txt" for c in chunk_index],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
