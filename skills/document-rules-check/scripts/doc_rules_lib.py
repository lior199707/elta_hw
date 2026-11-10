"""Deterministic core of the document-rules-check skill (no network, no model calls).

Mirrors the web app's backend (extraction, locations, chunking with overlap, verbatim-quote
verification) so both produce the same blocks; a parity test in the repository guards that.
"""

from __future__ import annotations

import json
import math
import re
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = (".docx", ".txt")
MAX_FILE_BYTES = 20 * 1024 * 1024
CHARS_PER_TOKEN = 4
BLOCK_ID_PREFIX = "B"
CHUNK_ID_PREFIX = "chunk-"
TABLE_CELL_SEPARATOR = " | "
SEVERITIES = ("high", "medium", "low")
RULE_ID_PATTERN = re.compile(r"^R[1-9][0-9]*$")
RULE_TITLE_MAX = 200
RULE_TEXT_MAX = 2000
BLOCKS_FILE = "blocks.json"
RULES_FILE = "rules.json"
CHUNKS_DIR = "chunks"
FINDINGS_DIR = "findings"
REPORT_MD = "report.md"
REPORT_JSON = "report.json"
_QUOTE_EQUIVALENTS = str.maketrans(
    {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " "}
)
_QUOTE_WRAPPERS = "\"'‘’“” "
_BLANK_LINE = re.compile(r"\n\s*\n")


class SkillError(Exception):
    """A problem the agent must report to the user; `code` is machine-readable."""

    def __init__(self, code: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


@dataclass
class Block:
    block_id: str
    index: int
    kind: str
    text: str
    heading_path: list[str] = field(default_factory=list)
    page: int | None = None
    section_position: int | None = None
    table_number: int | None = None
    table_row: int | None = None


# ------------------------------------------------------------------ extraction


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def validate_file(path: Path) -> None:
    if not path.is_file():
        raise SkillError("not_found", f"File not found: {path}", 3)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        shown = path.suffix or "(none)"
        raise SkillError(
            "unsupported_type", f"Unsupported file type '{shown}'. Supported: .docx, .txt.", 2
        )
    if path.stat().st_size > MAX_FILE_BYTES:
        raise SkillError("too_large", "The file is larger than 20 MB.", 5)


def extract_blocks(path: Path) -> list[Block]:
    """Validate and extract numbered blocks. Raises SkillError."""
    validate_file(path)
    raw = path.read_bytes()
    drafts = _docx_drafts(raw) if path.suffix.lower() == ".docx" else _txt_drafts(raw)
    blocks: list[Block] = []
    for draft in drafts:
        text = normalize_whitespace(draft.text)
        if text:
            index = len(blocks) + 1
            draft.text, draft.index, draft.block_id = text, index, f"{BLOCK_ID_PREFIX}{index}"
            blocks.append(draft)
    if not blocks:
        raise SkillError("empty", "The document contains no text to check.", 4)
    return blocks


def _txt_drafts(raw: bytes) -> list[Block]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SkillError("unreadable", "The text file is not valid UTF-8.", 3) from exc
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [p for p in _BLANK_LINE.split(unified) if p.strip()]
    return [Block("", 0, "paragraph", p, section_position=n) for n, p in enumerate(paragraphs, 1)]


def _docx_drafts(raw: bytes) -> list[Block]:
    from docx import Document
    from docx.opc.exceptions import PackageNotFoundError
    from docx.oxml.ns import qn
    from docx.table import Table
    from lxml.etree import XMLSyntaxError

    try:
        document = Document(BytesIO(raw))
    except (PackageNotFoundError, zipfile.BadZipFile, KeyError, ValueError, XMLSyntaxError) as exc:
        raise SkillError(
            "unreadable",
            "The file is not a readable DOCX document (corrupt, encrypted, or another format).",
            3,
        ) from exc

    page_break, text_tag = qn("w:lastRenderedPageBreak"), qn("w:t")
    has_layout = next(document.element.body.iter(page_break), None) is not None
    page = 1

    def advance(element: Any) -> int | None:
        nonlocal page
        start = None
        for node in element.iter(page_break, text_tag):
            if node.tag == page_break:
                page += 1
            elif start is None and node.text and node.text.strip():
                start = page
        return (start if start is not None else page) if has_layout else None

    drafts: list[Block] = []
    headings: list[str] = []
    position = table_number = 0
    for item in document.iter_inner_content():
        if isinstance(item, Table):
            table_number += 1
            for row_number, row in enumerate(item.rows, start=1):
                row_page = advance(row._tr)
                cells, previous = [], None
                for cell in row.cells:
                    if cell._tc is previous:
                        continue
                    previous = cell._tc
                    if text := normalize_whitespace(cell.text):
                        cells.append(text)
                drafts.append(
                    Block(
                        "",
                        0,
                        "table_row",
                        TABLE_CELL_SEPARATOR.join(cells),
                        list(headings),
                        row_page,
                        None,
                        table_number,
                        row_number,
                    )
                )
            continue
        item_page = advance(item._p)
        style = item.style.name if item.style is not None and item.style.name else ""
        level = style.removeprefix("Heading ")
        if style.startswith("Heading ") and level.isdigit() and item.text.strip():
            del headings[int(level) - 1 :]
            headings.append(normalize_whitespace(item.text))
            position = 0
            drafts.append(Block("", 0, "heading", item.text, list(headings), item_page))
        elif style == "Title":
            drafts.append(Block("", 0, "heading", item.text, [], item_page))
        elif item.text.strip():
            position += 1
            numbered = item._p.pPr is not None and item._p.pPr.numPr is not None
            kind = "list_item" if numbered or style.startswith("List") else "paragraph"
            drafts.append(Block("", 0, kind, item.text, list(headings), item_page, position))

    seen: set[tuple[str, str]] = set()
    for section in document.sections:
        for part, kind in ((section.header, "header"), (section.footer, "footer")):
            if part.is_linked_to_previous:
                continue
            for paragraph in part.paragraphs:
                key = (kind, normalize_whitespace(paragraph.text))
                if key not in seen:
                    seen.add(key)
                    drafts.append(Block("", 0, kind, paragraph.text))
    return drafts


# ------------------------------------------------------------------ locations and chunks


def describe_location(block: Block) -> str:
    parts = []
    if block.page is not None:
        parts.append(f"Page {block.page}")
    if block.heading_path:
        parts.append(f"Section: {' > '.join(block.heading_path)}")
    in_section = " in section" if block.heading_path else ""
    if block.kind == "table_row":
        parts.append(f"Table {block.table_number}, row {block.table_row}")
    elif block.kind in ("paragraph", "list_item") and block.section_position is not None:
        label = "Paragraph" if block.kind == "paragraph" else "List item"
        parts.append(f"{label} {block.section_position}{in_section}")
    elif block.kind in ("header", "footer"):
        parts.append(f"Page {block.kind}")
    elif block.kind == "heading":
        parts.append("Heading")
    return " | ".join(parts)


def render_line(block: Block) -> str:
    return f"[{block.block_id}] ({describe_location(block)}) {block.text}"


def build_chunks(blocks: list[Block], token_budget: int, overlap: int) -> list[list[Block]]:
    """Same algorithm as the backend: budget-bounded, `overlap` shared blocks, always progresses."""
    if token_budget < 1 or overlap < 0:
        raise SkillError("bad_arguments", "chunk tokens must be >= 1 and overlap >= 0", 1)
    costs = [math.ceil(len(render_line(block)) / CHARS_PER_TOKEN) for block in blocks]
    chunks: list[list[Block]] = []
    start = 0
    while start < len(blocks):
        end, total = start + 1, costs[start]
        while end < len(blocks) and total + costs[end] <= token_budget:
            total += costs[end]
            end += 1
        chunks.append(blocks[start:end])
        if end == len(blocks):
            break
        shared = min(overlap, end - start - 1)
        while shared > 0 and sum(costs[end - shared : end]) + costs[end] > token_budget:
            shared -= 1
        start = end - shared
    return chunks


def chunk_id(number: int) -> str:
    return f"{CHUNK_ID_PREFIX}{number:03d}"


# ------------------------------------------------------------------ rules


def load_rules(workspace: Path) -> list[dict[str, Any]]:
    """Validate rules.json (schema: references/rules.schema.json). Raises SkillError."""
    path = workspace / RULES_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SkillError("rules_missing", f"{path} does not exist.", 6) from exc
    except json.JSONDecodeError as exc:
        raise SkillError("rules_invalid", f"{path} is not valid JSON: {exc}", 6) from exc
    rules = data.get("rules") if isinstance(data, dict) else None
    problems: list[str] = []
    if not isinstance(rules, list) or not rules:
        raise SkillError("rules_invalid", "rules.json needs a non-empty 'rules' list.", 6)
    seen: set[str] = set()
    for position, rule in enumerate(rules, start=1):
        where = f"rule #{position}"
        if not isinstance(rule, dict):
            problems.append(f"{where} is not an object")
            continue
        rule_id = rule.get("id")
        if not isinstance(rule_id, str) or not RULE_ID_PATTERN.match(rule_id):
            problems.append(f"{where}: id must look like R1, R2, ...")
        elif rule_id in seen:
            problems.append(f"{where}: duplicate id {rule_id}")
        else:
            seen.add(rule_id)
        for key, limit in (("title", RULE_TITLE_MAX), ("text", RULE_TEXT_MAX)):
            value = rule.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                problems.append(f"{where}: '{key}' must be 1 to {limit} characters")
        for key in ("examples", "non_examples"):
            if key in rule and not (
                isinstance(rule[key], list) and all(isinstance(x, str) for x in rule[key])
            ):
                problems.append(f"{where}: '{key}' must be a list of strings")
    if problems:
        raise SkillError("rules_invalid", "; ".join(problems), 6)
    return rules


# ------------------------------------------------------------------ verification


def _canonical(text: str) -> str:
    translated = text.translate(_QUOTE_EQUIVALENTS)
    lowered = translated.lower()
    return lowered if len(lowered) == len(translated) else translated


def find_quote(text: str, quote: str) -> tuple[int, int] | None:
    haystack = _canonical(text)
    for variant in (
        normalize_whitespace(quote),
        normalize_whitespace(quote).strip(_QUOTE_WRAPPERS),
    ):
        if variant and (position := haystack.find(_canonical(variant))) >= 0:
            return position, position + len(variant)
    return None


def load_findings(workspace: Path, chunk_count: int) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (raw findings, chunk ids without a findings file). Raises SkillError on bad files."""
    findings: list[dict[str, Any]] = []
    missing: list[str] = []
    problems: list[str] = []
    for number in range(1, chunk_count + 1):
        path = workspace / FINDINGS_DIR / f"{chunk_id(number)}.json"
        if not path.is_file():
            missing.append(chunk_id(number))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: invalid JSON ({exc})")
            continue
        items = data.get("findings") if isinstance(data, dict) else None
        if not isinstance(items, list):
            problems.append(f"{path.name}: needs a 'findings' list (use [] when nothing found)")
            continue
        for position, item in enumerate(items, start=1):
            keys = ("rule_id", "block_id", "quote", "explanation", "severity")
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str) for k in keys):
                problems.append(f"{path.name} finding #{position}: needs string fields {keys}")
            elif item["severity"] not in SEVERITIES:
                problems.append(f"{path.name} finding #{position}: severity must be {SEVERITIES}")
            else:
                findings.append(item)
    if problems:
        raise SkillError("findings_invalid", "; ".join(problems), 7)
    return findings, missing


def verify(
    blocks: list[Block], rules: list[dict[str, Any]], findings: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Keep findings whose quote is verbatim in the document; dedupe; order by position."""
    rule_ids = {rule["id"] for rule in rules}
    by_id = {block.block_id: block for block in blocks}
    kept: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    dropped: list[dict[str, str]] = []
    for item in findings:
        reason = None
        if item["rule_id"] not in rule_ids:
            reason = "unknown rule id"
        elif not normalize_whitespace(item["quote"]).strip(_QUOTE_WRAPPERS):
            reason = "empty quote"
        else:
            referenced = [by_id[item["block_id"]]] if item["block_id"] in by_id else []
            order = referenced + [b for b in blocks if b.block_id != item["block_id"]]
            match = next(((b, s) for b in order if (s := find_quote(b.text, item["quote"]))), None)
            if match is None:
                reason = "quote not found verbatim in the document"
            else:
                block, (start, end) = match
                key = (item["rule_id"], block.block_id, start, end)
                kept.setdefault(
                    key,
                    {
                        **item,
                        "block_id": block.block_id,
                        "quote": block.text[start:end],
                        "start": start,
                        "end": end,
                        "corrected_from": (
                            item["block_id"] if item["block_id"] != block.block_id else None
                        ),
                    },
                )
        if reason:
            dropped.append(
                {"rule_id": item["rule_id"], "block_id": item["block_id"], "reason": reason}
            )
    items = list(kept.values())
    outermost = [
        v
        for v in items
        if not any(
            o is not v
            and o["rule_id"] == v["rule_id"]
            and o["block_id"] == v["block_id"]
            and o["start"] <= v["start"]
            and v["end"] <= o["end"]
            for o in items
        )
    ]
    outermost.sort(key=lambda v: (by_id[v["block_id"]].index, v["start"], v["rule_id"]))
    return outermost, dropped


# ------------------------------------------------------------------ report


def build_report(
    meta: dict[str, Any],
    blocks: list[Block],
    rules: list[dict[str, Any]],
    violations: list[dict[str, Any]],
    dropped: list[dict[str, str]],
    missing: list[str],
) -> dict[str, Any]:
    by_id = {block.block_id: block for block in blocks}
    return {
        "document_name": meta["document"],
        "status": "partial" if missing else "completed",
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "block_count": len(blocks),
        "chunks_total": meta["chunk_count"],
        "chunks_not_checked": missing,
        "has_page_layout": meta["has_page_layout"],
        "rules": rules,
        "violations": [
            {
                **v,
                "location": describe_location(by_id[v["block_id"]]),
                "block": asdict(by_id[v["block_id"]]),
            }
            for v in violations
        ],
        "dropped": dropped,
    }


def render_markdown(report: dict[str, Any]) -> str:
    violations = report["violations"]
    severities = {s: sum(v["severity"] == s for v in violations) for s in SEVERITIES}
    status = (
        "Completed"
        if report["status"] == "completed"
        else (f"PARTIAL: {len(report['chunks_not_checked'])} chunk(s) were not checked")
    )
    lines = [
        f"# Document rules check: {report['document_name']}",
        "",
        f"- **Status:** {status}",
        f"- **Checked at (UTC):** {report['checked_at']}",
        f"- **Violations:** {len(violations)} (high {severities['high']}, "
        f"medium {severities['medium']}, low {severities['low']})",
        f"- **Rules:** {len(report['rules'])} | **Blocks:** {report['block_count']} | "
        f"**Chunks:** {report['chunks_total']}",
        "",
        "> "
        + (
            "Page numbers come from the layout Microsoft Word saved in the file."
            if report["has_page_layout"]
            else "Page numbers are not shown: the file has no saved Word page layout. "
            "Locations use section, paragraph and table row."
        ),
        "",
        "## Summary",
        "",
        "| Rule | Title | Violations | Result |",
        "|---|---|---|---|",
    ]
    for rule in report["rules"]:
        count = sum(v["rule_id"] == rule["id"] for v in violations)
        result = (
            "Violations found"
            if count
            else ("Passed" if report["status"] == "completed" else "No violations in checked parts")
        )
        lines.append(f"| {rule['id']} | {rule['title']} | {count} | {result} |")
    for rule in report["rules"]:
        own = [v for v in violations if v["rule_id"] == rule["id"]]
        if not own:
            continue
        lines += ["", f"## {rule['id']}: {rule['title']} ({len(own)})"]
        for number, v in enumerate(own, start=1):
            text = v["block"]["text"]
            highlighted = f"{text[: v['start']]}**{text[v['start'] : v['end']]}**{text[v['end'] :]}"
            lines += [
                "",
                f"### {number}. {v['severity'].capitalize()} severity",
                "",
                f"*Location:* {v['location']}",
                "",
                f"> {highlighted}",
                "",
                v["explanation"],
            ]
    lines += ["", "## Coverage", ""]
    if report["chunks_not_checked"]:
        lines.append(f"- Not checked: {', '.join(report['chunks_not_checked'])}")
    else:
        lines.append("- Every chunk was checked.")
    lines.append(f"- Findings dropped by verification: {len(report['dropped'])}")
    lines += [f"  - {d['rule_id']} / {d['block_id']}: {d['reason']}" for d in report["dropped"]]
    corrected = [v for v in violations if v.get("corrected_from")]
    lines.append(f"- Block ids corrected by verification: {len(corrected)}")
    lines += [
        f"  - {v['rule_id']}: {v['corrected_from']} -> {v['block_id']} (quote found there)"
        for v in corrected
    ]
    return "\n".join(lines) + "\n"
