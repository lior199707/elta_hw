# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx>=1.2"]
# ///
"""Validate rules, verify the agent's findings and write report.md + report.json.

Usage:
  uv run scripts/verify.py <workspace> --rules-only   # check rules.json before reviewing
  uv run scripts/verify.py <workspace>                # verify findings/ and write the report
Prints one JSON object. Exit codes: 0 ok (completed or partial), 1 workspace missing,
6 invalid rules.json, 7 invalid findings file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_rules_lib import (  # noqa: E402
    BLOCKS_FILE,
    REPORT_JSON,
    REPORT_MD,
    Block,
    SkillError,
    build_report,
    load_findings,
    load_rules,
    render_markdown,
    verify,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--rules-only", action="store_true")
    args = parser.parse_args()
    workspace: Path = args.workspace.resolve()

    try:
        if not (workspace / BLOCKS_FILE).is_file():
            raise SkillError(
                "workspace_missing", f"No {BLOCKS_FILE} in {workspace}; run extract.py first.", 1
            )
        rules = load_rules(workspace)
        if args.rules_only:
            print(json.dumps({"ok": True, "rules": [r["id"] for r in rules]}))
            return 0
        meta = json.loads((workspace / BLOCKS_FILE).read_text(encoding="utf-8"))
        blocks = [Block(**block) for block in meta["blocks"]]
        findings, missing = load_findings(workspace, meta["chunk_count"])
    except SkillError as exc:
        print(json.dumps({"ok": False, "code": exc.code, "error": str(exc)}))
        return exc.exit_code

    violations, dropped = verify(blocks, rules, findings)
    report = build_report(meta, blocks, rules, violations, dropped, missing)
    (workspace / REPORT_JSON).write_text(json.dumps(report, indent=1), encoding="utf-8")
    (workspace / REPORT_MD).write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "status": report["status"],
                "violations": len(violations),
                "per_rule": {
                    r["id"]: sum(v["rule_id"] == r["id"] for v in violations) for r in rules
                },
                "dropped": len(dropped),
                "chunks_not_checked": missing,
                "report": str(workspace / REPORT_MD),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
