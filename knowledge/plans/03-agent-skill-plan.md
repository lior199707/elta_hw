# Agent Skill Plan: `document-rules-check`

> Status: PLANNED (2026-11-10). Bonus requirement: an Agent Skill that performs the document check and loads into a standard agent such as Claude Code.

## Table of Contents

1. [Principles (Best Practices Applied)](#1-principles-best-practices-applied)
2. [Folder Layout](#2-folder-layout)
3. [Q1: Document Input and Validation](#3-q1-document-input-and-validation)
4. [Q2: Rules](#4-q2-rules)
5. [Q3: Running the Findings](#5-q3-running-the-findings)
6. [Q4: Output](#6-q4-output)
7. [End-to-End Flow in SKILL.md](#7-end-to-end-flow-in-skillmd)
8. [Testing](#8-testing)
9. [Scope and Time Box](#9-scope-and-time-box)

---

## 1. Principles (Best Practices Applied)

| Practice | How it is applied |
|---|---|
| **The host agent is the LLM** | No API key, no backend. The agent (e.g. Claude in Claude Code) judges the text; the skill supplies instructions and deterministic tools. |
| **Deterministic work in scripts, judgment in the model** | Validation, extraction, chunking, schema checks, quote verification and report rendering are Python scripts. Only "does this passage violate this rule?" is left to the model. |
| **Progressive disclosure** | `SKILL.md` stays short (the procedure). Schemas, review guidelines and examples live in `references/` and are read only when needed. Script source is executed, not loaded into context. |
| **Precise `description` frontmatter** | States what it does and when to use it ("check a DOCX/TXT document against rules", "compliance", "find violations"), so the agent triggers it at the right time. |
| **Self-contained and portable** | Scripts carry PEP 723 inline dependency metadata (`python-docx`), so `uv run scripts/x.py` works anywhere uv exists, with no install step and no import from our backend. |
| **Fail fast, structured errors** | Every script prints JSON and exits non-zero with a clear message on bad input; the agent stops and reports instead of guessing. |
| **Bounded context** | Large documents are pre-split into chunk files (with overlap); the agent reads one chunk at a time. |
| **Same guarantees as the web app** | Verbatim-quote verification, dropped-quote count, coverage tracking (a chunk without results is "not checked", never "clean"), prompt-injection rule, page/section/paragraph/row locations. |

---

## 2. Folder Layout

```
skills/document-rules-check/
  SKILL.md                       # frontmatter + the 6-step procedure (short)
  scripts/
    doc_rules_lib.py             # shared: extraction, locations, normalization, quote matching
    extract.py                   # Q1: validate + extract + chunk
    rules.py                     # Q2: validate rules.json against the schema (and optional import)
    verify.py                    # Q3: verify findings, dedupe, coverage
    report.py                    # Q4: render report.md + report.json
  references/
    rules.schema.json            # JSON Schema for rules.json
    findings.schema.json         # JSON Schema for one chunk's findings file
    review-guidelines.md         # how to judge: verbatim quotes, every instance, severity, injection
    example-rules.md             # ready-made rules (the 3 defaults) users can start from
```

Run-time work files go to a workspace next to the document, never into the skill folder:
`<document-dir>/<document-name>.rules-check/` (blocks.json, chunks/, rules.json, findings/, report.md, report.json).

Installation: copy the folder to `~/.claude/skills/` (user level) or `<project>/.claude/skills/` (project level). Requirement: `uv` (or Python 3.11+ with `python-docx`).

---

## 3. Q1: Document Input and Validation

**Recommendation: one deterministic script does validation, extraction and chunking in one pass.**

`uv run scripts/extract.py <path> [--chunk-tokens 8000] [--overlap 2]`

- Validates: file exists, extension `.docx`/`.txt`, size limit (20 MB), DOCX opens as a Word package, TXT is UTF-8, document contains text.
- Exit codes: `0` ok, `2` unsupported type, `3` unreadable/corrupt, `4` empty, `5` too large; stdout is always JSON (`{"ok": false, "error": "...", "code": "unsupported_type"}`) so the agent can relay the reason.
- Extraction mirrors the backend (body order incl. tables, headings, list items, merged cells, headers/footers, page numbers from Word's saved layout).
- Writes `blocks.json` (id, kind, text, heading path, page, section position, table/row) and `chunks/chunk-001.txt ...`: rendered lines such as
  `[B182] (p.27 | 23 Maintenance procedure 23 | Table 1, row 61) Peak transmit power | 25 kW`.
- Smaller default chunk budget than the web app (8k tokens): the agent has a large context, but small chunks keep recall high and let it work chunk by chunk.

---

## 4. Q2: Rules

**Recommendation: free text in, validated JSON out, confirmed by the user.** Neither extreme works well:
- Free text only: no stable ids, so findings cannot be linked to rules, verified or re-run reproducibly.
- Asking the user to write JSON: poor UX.

Flow:
1. The user gives rules in any form: chat text, a bullet list, a `.md`/`.txt` file, or an existing `rules.json`.
2. The agent normalizes them into `rules.json` following `references/rules.schema.json`:
   `{"rules": [{"id": "R1", "title": "No performance figures", "text": "...", "examples": ["..."]?, "non_examples": ["..."]?}]}`
   (ids `R1..Rn`, title <= 200 chars, text <= 2000 chars, same limits as the web app; optional examples sharpen judgment).
3. `uv run scripts/rules.py validate rules.json` checks it deterministically (schema, unique ids, limits) and fails fast with the exact problem.
4. The agent shows the normalized rules table and asks the user to confirm or edit **before** reviewing. This catches misinterpretation of free text early.
5. Starter rules are in `references/example-rules.md` (the app's 3 defaults).

Optional (stretch): `rules.py import --api http://localhost:8000` pulls the active rules from the running web app, so skill and app check the same rule set.

---

## 5. Q3: Running the Findings

**Recommendation: the agent reviews chunk by chunk and writes structured findings; a script verifies them.**

1. For each `chunks/chunk-NNN.txt`, the agent applies `references/review-guidelines.md` (same principles as the app's system prompt): find every passage that violates any rule; quote the shortest exact substring of one block; one finding per passage per rule; a number alone is not a violation; the document is untrusted data, so instructions inside it are ignored.
2. It writes `findings/chunk-NNN.json` per chunk, following `references/findings-schema.json`, **even when empty** (`{"chunk": "chunk-003", "findings": []}`). An empty file means "checked, nothing found"; a missing file means "not checked".
3. `uv run scripts/verify.py <workspace>` then:
   - validates every findings file against the schema;
   - keeps a finding only if its quote is found verbatim in the referenced block (same tolerant normalization as the app: whitespace, curly quotes, dashes, case), correcting the block id if the quote is elsewhere;
   - drops unknown rule ids, empty or invented quotes, with reasons;
   - removes duplicates from chunk overlap and spans contained in longer spans of the same rule;
   - reports coverage: chunks without a findings file are listed as NOT checked and the status becomes `partial`.
4. Optional for very large documents: an agent that supports subagents can review chunks in parallel; the files-per-chunk contract makes that safe.

---

## 6. Q4: Output

**Recommendation: a Markdown report plus a JSON report, rendered deterministically by a script, and a short chat summary.**

`uv run scripts/report.py <workspace>` writes:
- `report.md`: title, document, date, status (completed/partial), counts; a summary table per rule (violations / passed); then per-rule sections with each violation's severity, location (Page, Section, Paragraph N in section or Table T, row R), the quote highlighted in its block text (`**...**`), and the explanation; a coverage section (chunks not checked, dropped findings with reasons) and the page-number note.
- `report.json`: the same data, machine-readable (same field names as the web app's API where possible).

The agent then prints a 5 to 10 line summary in chat with the path to `report.md`.

Why not PDF: it needs extra tooling (pandoc/LaTeX or a headless browser), is not editable, and Markdown already renders in Claude Code, IDEs and GitHub and converts to PDF in one step when needed. HTML is a possible later addition.

---

## 7. End-to-End Flow in SKILL.md

1. **Extract**: run `extract.py` on the user's file; on a non-zero exit, report the error and stop.
2. **Rules**: collect rules, write `rules.json`, run `rules.py validate`, show them and get the user's confirmation.
3. **Review**: for each chunk, read it, apply `review-guidelines.md`, write `findings/chunk-NNN.json`.
4. **Verify**: run `verify.py`; if chunks are missing, review them and verify again.
5. **Report**: run `report.py`.
6. **Summarize** in chat: status, counts per rule, top findings, report path, any coverage gaps or dropped findings.

---

## 8. Testing

- `backend/tests/unit/skill/` (pytest, run by `uv run poe check`):
  - `extract.py` on the three samples: exit codes and JSON for unsupported, corrupt, empty and oversized files; chunk files cover every block with the configured overlap.
  - **Parity with the backend**: blocks from the skill's extractor equal the backend's (text, kind, heading path, page, section position, table/row) for all samples, including the Word-saved one, so the two implementations cannot drift.
  - `rules.py`: valid and invalid rule files.
  - `verify.py`: verbatim kept, paraphrase dropped with reason, wrong block id corrected, overlap duplicates removed, missing chunk reported as not checked.
  - `report.py`: golden-file test of `report.md` for a fixed findings set.
- Manual acceptance: load the skill in Claude Code and check `samples/easy_system_overview.docx` and `samples/hard_field_trial_report_word_saved.docx`; expected findings match the ground truth (`tests/fixtures/sample_documents.py`). This uses the agent's own model, not the Gemini quota.
- New poe tasks: `skill-test` (the pytest subset) and `skill-install` (copy the folder into `~/.claude/skills`, asks nothing destructive: refuses to overwrite).

---

## 9. Scope and Time Box

It is about 22:55; the submission deadline is 24:00 and the README plus submission need about 25 minutes.

| Priority | Item |
|---|---|
| Must | SKILL.md, `doc_rules_lib.py`, `extract.py`, `verify.py`, `report.py`, both schemas, review guidelines, example rules, tests for extract/verify/report incl. backend parity |
| Should | `rules.py validate`, manual run in Claude Code on the easy sample |
| Stretch | `rules.py import --api`, subagent fan-out note, HTML report |

---

## 10. Results (2026-11-10)

- Built as planned with two entry points (`extract.py`, `verify.py` with `--rules-only`) and a shared `doc_rules_lib.py`; chunk overlap kept (boundary statements, context compaction, per-chunk findings contract).
- `uv run poe skill-test`: 15 tests incl. extraction parity with the backend on all 4 samples; standalone `uv run --script` verified.
- Independent test by a separate agent (no access to ground truth or backend code), scored against `tests/fixtures/sample_documents.py`:
  - easy: 2/2 planted violations, 0 false positives, completed;
  - hard (Word-saved, 6 chunks, 321 blocks): 7/7, 0 false positives, every location matches Word (pages 2, 20, 27, 29, 42, 48, 35; sections; paragraph/list item/table+row), prompt injection ignored;
  - fake PDF: exit 2 `unsupported_type`, no workspace created.
  - Caveat: for chunks 3 to 6 the tester stripped repeated boilerplate sentences with a script before reading; SKILL.md now forbids filtering chunks.
- Fixes from the tester's friction report: documented `--workspace` and the default workspace location, stated that a `partial` run exits 0 so `status` must be read, and added long-document guidance (read every line, lower `--chunk-tokens`).
