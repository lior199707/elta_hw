"""The Agent Skill's deterministic scripts (skills/document-rules-check/scripts)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from doc_checker.extraction.document_extraction import extract_document

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "skills" / "document-rules-check" / "scripts"
SAMPLES = REPO_ROOT / "samples"
SAMPLE_FILES = sorted(SAMPLES.glob("*.docx"))
RULES = {
    "rules": [
        {"id": "R1", "title": "No performance figures", "text": "No performance numbers."},
        {"id": "R2", "title": "No personal names", "text": "No names of people."},
    ]
}


def load_lib() -> ModuleType:
    spec = importlib.util.spec_from_file_location("doc_rules_lib", SCRIPTS / "doc_rules_lib.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["doc_rules_lib"] = module
    spec.loader.exec_module(module)
    return module


def run(script: str, *args: str) -> tuple[int, dict[str, object]]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True, check=False
    )
    return completed.returncode, json.loads(completed.stdout)


def extract(document: Path, workspace: Path, *extra: str) -> dict[str, object]:
    code, output = run("extract.py", str(document), "--workspace", str(workspace), *extra)
    assert code == 0, output
    return output


def write_findings(workspace: Path, chunk: str, findings: list[dict[str, str]]) -> None:
    (workspace / "findings" / f"{chunk}.json").write_text(
        json.dumps({"chunk": chunk, "findings": findings}), encoding="utf-8"
    )


def finding(block_id: str, quote: str, rule_id: str = "R1") -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "block_id": block_id,
        "quote": quote,
        "explanation": "why",
        "severity": "high",
    }


@pytest.mark.parametrize("sample", SAMPLE_FILES, ids=lambda p: p.name)
def test_skill_extraction_matches_the_backend(sample: Path) -> None:
    lib = load_lib()

    skill_blocks = lib.extract_blocks(sample)
    backend_blocks = extract_document(sample.name, sample.read_bytes()).blocks

    assert [
        (
            b.block_id,
            b.kind,
            b.text,
            tuple(b.heading_path),
            b.page,
            b.section_position,
            b.table_number,
            b.table_row,
        )
        for b in skill_blocks
    ] == [
        (
            b.block_id,
            b.kind.value,
            b.text,
            b.heading_path,
            b.page,
            b.section_position,
            b.table_number,
            b.table_row,
        )
        for b in backend_blocks
    ]


@pytest.mark.parametrize(
    ("name", "content", "code", "error_code"),
    [
        ("report.pdf", b"%PDF-1.4", 2, "unsupported_type"),
        ("README", b"text", 2, "unsupported_type"),
        ("disguised.docx", b"%PDF-1.4", 3, "unreadable"),
        ("latin1.txt", b"caf\xe9 \xff", 3, "unreadable"),
        ("blank.txt", b"  \n\n \t ", 4, "empty"),
    ],
)
def test_extract_rejects_bad_files_with_codes(
    tmp_path: Path, name: str, content: bytes, code: int, error_code: str
) -> None:
    document = tmp_path / name
    document.write_bytes(content)

    exit_code, output = run("extract.py", str(document))

    assert (exit_code, output["ok"], output["code"]) == (code, False, error_code)
    assert not (tmp_path / f"{document.stem}.rules-check").exists()


def test_extract_reports_missing_file(tmp_path: Path) -> None:
    exit_code, output = run("extract.py", str(tmp_path / "nope.docx"))

    assert (exit_code, output["code"]) == (3, "not_found")


def test_chunks_cover_every_block_with_overlap(tmp_path: Path) -> None:
    sample = SAMPLES / "hard_field_trial_report_word_saved.docx"

    output = extract(sample, tmp_path / "ws", "--chunk-tokens", "4000")

    meta = json.loads((tmp_path / "ws" / "blocks.json").read_text(encoding="utf-8"))
    chunk_files = sorted((tmp_path / "ws" / "chunks").glob("chunk-*.txt"))
    seen = {
        line.split("]")[0][1:]
        for path in chunk_files
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
    }
    assert output["chunk_count"] == len(chunk_files) > 1
    assert seen == {block["block_id"] for block in meta["blocks"]}
    assert meta["has_page_layout"] is True
    first, second = meta["chunks"][0], meta["chunks"][1]
    assert int(second["first_block"][1:]) == int(first["last_block"][1:]) - 1, "2-block overlap"


def test_rules_only_accepts_valid_and_rejects_invalid_rules(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    extract(SAMPLES / "easy_system_overview.docx", workspace)
    (workspace / "rules.json").write_text(json.dumps(RULES), encoding="utf-8")

    expected = (0, {"ok": True, "rules": ["R1", "R2"]})
    assert run("verify.py", str(workspace), "--rules-only") == expected

    duplicate = {"id": "R1", "title": "", "text": "y"}
    bad = {"rules": [{"id": "R1", "title": "A", "text": "x"}, duplicate]}
    (workspace / "rules.json").write_text(json.dumps(bad), encoding="utf-8")
    code, output = run("verify.py", str(workspace), "--rules-only")
    assert code == 6
    assert "duplicate id R1" in str(output["error"]) and "'title'" in str(output["error"])


def test_verify_keeps_verbatim_drops_invented_and_writes_report(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    extract(SAMPLES / "easy_system_overview.docx", workspace)
    (workspace / "rules.json").write_text(json.dumps(RULES), encoding="utf-8")
    write_findings(
        workspace,
        "chunk-001",
        [
            finding("B4", "50 KM"),
            finding("B1", "every 2 seconds"),
            finding("B4", "range is 80 km"),
            finding("B4", "50 km", rule_id="R9"),
            finding("B4", "maximum detection range is 50 km"),
        ],
    )

    code, output = run("verify.py", str(workspace))

    report = json.loads((workspace / "report.json").read_text(encoding="utf-8"))
    assert code == 0 and output["status"] == "completed"
    assert [(v["block_id"], v["quote"]) for v in report["violations"]] == [
        ("B4", "maximum detection range is 50 km"),
        ("B5", "every 2 seconds"),
    ]
    assert sorted(d["reason"] for d in report["dropped"]) == [
        "quote not found verbatim in the document",
        "unknown rule id",
    ]
    markdown = (workspace / "report.md").read_text(encoding="utf-8")
    assert "| R2 | No personal names | 0 | Passed |" in markdown
    assert "The **maximum detection range is 50 km**." in markdown


def test_missing_chunk_findings_make_the_report_partial(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    hard = SAMPLES / "hard_field_trial_report_word_saved.docx"
    extract(hard, workspace, "--chunk-tokens", "4000")
    (workspace / "rules.json").write_text(json.dumps(RULES), encoding="utf-8")
    write_findings(workspace, "chunk-001", [])

    code, output = run("verify.py", str(workspace))

    assert code == 0 and output["status"] == "partial"
    not_checked = output["chunks_not_checked"]
    assert isinstance(not_checked, list) and "chunk-002" in not_checked
    markdown = (workspace / "report.md").read_text(encoding="utf-8")
    assert "PARTIAL" in markdown and "No violations in checked parts" in markdown


def test_malformed_findings_file_fails_fast(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    extract(SAMPLES / "easy_system_overview.docx", workspace)
    (workspace / "rules.json").write_text(json.dumps(RULES), encoding="utf-8")
    write_findings(workspace, "chunk-001", [{"rule_id": "R1", "severity": "extreme"}])

    code, output = run("verify.py", str(workspace))

    assert (code, output["code"]) == (7, "findings_invalid")


def test_corrected_block_ids_are_recorded_and_reported(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    extract(SAMPLES / "easy_system_overview.docx", workspace)
    (workspace / "rules.json").write_text(json.dumps(RULES), encoding="utf-8")
    write_findings(workspace, "chunk-001", [finding("B1", "50 km")])

    run("verify.py", str(workspace))

    report = json.loads((workspace / "report.json").read_text(encoding="utf-8"))
    violation = report["violations"][0]
    assert (violation["block_id"], violation["corrected_from"]) == ("B4", "B1")
    markdown = (workspace / "report.md").read_text(encoding="utf-8")
    assert "Block ids corrected by verification: 1" in markdown
    assert "R1: B1 -> B4" in markdown
