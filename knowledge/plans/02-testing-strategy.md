# Testing Strategy

> Status: ACTIVE (2026-11-10). Complements the unit tests written during TDD (backend 186, frontend 92 + 4 E2E).

## Table of Contents

1. [Goals and Scope](#1-goals-and-scope)
2. [Test Tiers](#2-test-tiers)
3. [Area 1: Rules Lifecycle](#3-area-1-rules-lifecycle)
4. [Area 2: Sample Documents, Extraction and Chunking](#4-area-2-sample-documents-extraction-and-chunking)
5. [Area 3: Data Sent to the LLM and LLM Answers](#5-area-3-data-sent-to-the-llm-and-llm-answers)
6. [Commands](#6-commands)
7. [Known Limitations (Asserted, Not Hidden)](#7-known-limitations-asserted-not-hidden)

---

## 1. Goals and Scope

| # | Area | Question the tests answer |
|---|---|---|
| 1 | Rules | Can a user add, deactivate, reactivate and delete rules, and does the active set really decide what a check uses? |
| 2 | Documents | Is every sentence of easy, medium and hard DOCX files extracted exactly once, in order, and does chunking keep every block (and every boundary-crossing pair) whole? |
| 3 | LLM | Is the right data (all blocks, all selected rules, the schema) sent to Gemini, and does the real model find planted violations without flagging harmless numbers? |

Terminology: DOCX has no fixed pages. "Data split across pages" is modeled with explicit page breaks (`w:br type="page"`) inside and between paragraphs, and a table long enough to span pages when Word renders it.

---

## 2. Test Tiers

| Tier | Network | Gemini quota | Runs in | Purpose |
|---|---|---|---|---|
| T1 Unit (existing TDD tests) | none | 0 | `poe check`, `poe fe-check` | Each module in isolation |
| T2 Sample-document tests | none | 0 | `poe check` | Easy / medium / hard DOCX through extraction, chunking and the checker with a **spy** LLM |
| T3 Full-stack rules E2E | local backend only | 0 | `poe fe-e2e-backend` | Real browser + real API + real SQLite for the rules lifecycle |
| T4 Live LLM evaluation | Gemini | about 4 to 6 requests | `poe eval-live` | Real model on the three samples, scored against ground truth. **Only run with the user's go-ahead.** |

Mocked E2E (`poe fe-e2e`) stays hermetic; the full-stack project is separate so the default E2E run never needs a backend.

---

## 3. Area 1: Rules Lifecycle

**Backend scenario test (T2, API level, fake LLM):** one test walks the whole lifecycle and checks the effect on checks, not only on the rules list:
1. Add rule X: appears in `GET /api/rules?active=true`; a check sends `R<x>` to the model.
2. Deactivate X: gone from the active list, still in the full list; a default check does **not** send it; an explicit `rule_ids=[x]` check still can.
3. Reactivate X: back in the active list; a default check sends it again.
4. Delete X: gone everywhere; an explicit `rule_ids=[x]` check returns 404 and makes no model call.
5. Past checks keep X's snapshot after deletion.

**Full-stack E2E (T3, Playwright, no mocks, no Gemini):** against the running backend on `localhost:8000`:
add a uniquely named rule, see it on the Check page, deactivate it (it disappears from the Check page), reactivate it (it reappears), delete it (gone from Rules and Check). The test cleans up after itself so the developer's database is unchanged.

---

## 4. Area 2: Sample Documents, Extraction and Chunking

One builder module (`backend/tests/fixtures/sample_documents.py`) is the single source of truth. It builds each DOCX deterministically and declares its ground truth: planted violations (rule + text that must appear in a reported quote), sentences that must be extracted intact, and harmless "must not flag" phrases. `uv run poe samples` writes the same files to `samples/` for manual testing and the reviewer.

All content is fictional (system "Sentinel-7", people, sites).

| Level | Size | Structures | Planted violations | Distractors (must not flag) |
|---|---|---|---|---|
| Easy | 6 paragraphs, 1 chunk | heading, paragraphs | 2 performance figures | version number, issue date, course length |
| Medium | ~25 blocks, 1 chunk | title, nested headings, spec table, bullet list, header/footer | performance (table + list), 2 personal names, 1 test site | section and annex references, ISO number, approval date, revision footer |
| Hard | ~140k characters, **multiple chunks at the default 30k-token budget** | 45 sections, page-break paragraphs, a page break **inside** a sentence, a number split across bold/plain runs, a sentence continuing after a page break in the next paragraph, an 80-row table spanning pages with a violation near row 60, merged-cell signature row, list items, header/footer, a prompt-injection paragraph | performance (5, including the split cases), names, site | spare-part quantities, section numbers, dates, the injection text itself |

**Extraction assertions (T2):** every "must be intact" sentence appears in exactly one block, unbroken (page break inside a sentence, split runs); page-break-only paragraphs produce no block; table rows are blocks with the section's heading path; header/footer appear once; block ids are sequential.

**Chunking assertions (T2):** for budgets 2k, 8k and the default 30k tokens with overlap 2:
the hard document yields more than one chunk at the default budget; every block is in at least one chunk; no chunk exceeds the budget; the "sentence continued after a page break" pair (two consecutive blocks) appears together in at least one chunk; every planted-violation block appears whole.

---

## 5. Area 3: Data Sent to the LLM and LLM Answers

**Data-flow tests (T2, spy LLM, no network):**
- Run the real `ComplianceChecker` on each sample with a spy `LlmClient` that records every `(rules, chunk)` call.
- The union of all chunk blocks equals all document blocks; every call carries all selected rules with `R<id>` ids.
- The rendered prompt (`build_user_prompt`) contains each rule line in `<rules>` and each block line `[Bn] (heading path) text` in `<document>`, in order, and nothing else.
- With the real `GeminiLlmClient` and a fake SDK `models` API: the request carries the system instruction, JSON mime type, the `LlmViolationReport` schema and the configured temperature, and `contents` equals the built prompt.
- A spy that returns the planted quotes produces exactly the planted violations after verification (pipeline wiring end to end).

**Live evaluation (T4, opt-in):** runs the three samples through the real pipeline with the three default rules and prints a scorecard per document: recall of planted violations, must-not-flag hits (false positives), dropped (unverified) quotes, chunks, failed chunks, models used, duration. Pass bar: easy 100% recall and no false positives; medium and hard at least 75% recall, no false positives, no failed chunks. Cost: one request per chunk (about 4 to 6 total).

---

## 6. Commands

| Command | Tier |
|---|---|
| `uv run poe check` | T1 + T2 backend |
| `uv run poe fe-check` / `fe-e2e` | T1 frontend, mocked E2E |
| `uv run poe fe-e2e-backend` | T3 (needs `uv run poe up`) |
| `uv run poe samples` | Write easy/medium/hard DOCX to `samples/` |
| `uv run poe eval-live` | T4 (real Gemini, quota) |

---

## 7. Known Limitations (Asserted, Not Hidden)

- Text in text boxes and in tables nested inside table cells is not extracted (documented; out of scope for the samples).
- A sentence split across two paragraphs can only be quoted per block; the verifier accepts a quote from either block.
- Page numbers are not available from DOCX; locations are heading path + paragraph number.

---

## 8. Results Log

| Date | Tier | Command | Result |
|---|---|---|---|
| 2026-11-10 | T1 + T2 backend | `uv run poe check` | 226 passed (40 new: sample extraction, chunking, LLM data flow, rules lifecycle) |
| 2026-11-10 | T1 frontend | `uv run poe fe-check` | 92 passed, lint/format/types clean |
| 2026-11-10 | Mocked E2E | `uv run poe fe-e2e` | 4 passed |
| 2026-11-10 | T3 full-stack E2E | `uv run poe fe-e2e-backend` | 1 passed; database left unchanged (3 rules before and after) |
| 2026-11-10 | T3 persistence E2E | `uv run poe fe-e2e-backend` | Rule added in the browser survives `docker compose restart backend` (container restart verified in logs); backend project now runs with 1 worker so the restart cannot disturb other tests. Manually verified too: restart, stop/start and `down`/`up --build` all keep data (named volume `backend-data`); only `down -v` / volume removal deletes it |
| 2026-11-10 | T4 live, easy | `uv run poe eval-live -k easy` | PASS: 1 chunk, gemini-3.5-flash, recall 2/2 (`50 km` high, `2 seconds` medium), 0 false positives, 0 dropped, 19.9 s |
| 2026-11-10 | T4 live, medium | `uv run poe eval-live -k medium` | PASS: 1 chunk, gemini-3.5-flash, recall 6/6 after the scorer fix (first printed 5/6: the model quoted the minimal `300` for `300 simultaneous tracks`), 0 false positives, 0 dropped, 23.2 s |
| 2026-11-10 | Scorer fix | `tests/fixtures/live_scoring.py` | Quote and planted phrase match when either contains the other (both for recall and false positives); unit-tested with the real medium answer |
| 2026-11-10 | T4 live, hard | `uv run poe eval-live -k hard` | PASS: 2 chunks, models gemini-3.5-flash + gemini-3.5-flash-lite (live fallback on one chunk), recall 6/7, 0 false positives, 0 dropped, 40.2 s. Prompt injection ignored. Missed `4,000 hours` (MTBF): extraction kept the page-break sentence whole and the block was sent, so this is a model judgment; the default rule's wording does not explicitly cover reliability figures. Split-pair case: both halves flagged (`drops to`, `35 km`). |

**Live evaluation total:** 4 requests, 3/3 documents pass; overall recall 14/15 (93%), 0 false positives, 0 unverified quotes.

**Possible improvement (not applied, to avoid tuning to the test):** add reliability metrics (for example MTBF) to the default performance rule's wording.

Sample sizes: easy 6 blocks / 1 chunk, medium 23 blocks / 1 chunk, hard 321 blocks (138k characters) / 2 chunks at the default 30k-token budget.

### Page numbers (added 2026-11-10)

- Source: `w:lastRenderedPageBreak` markers that Microsoft Word writes when it saves a file. A block's page is where its first text starts. Files with no markers (generated, Google Docs, LibreOffice) get `page = null`; pages are never guessed.
- Unit tests insert real markers (start of paragraph, middle of paragraph, empty paragraph, table rows, header/footer, TXT).
- Ground truth: `samples/hard_field_trial_report_word_saved.docx` was produced by opening the hard sample in Microsoft Word (automation, read-only source) and saving a copy. Word reports 49 pages; for all 8 planted passages the computed start page equals the page Word reports via `Range.Information` (2, 20, 27, 28, 29, 42, 35, 48). Pinned as a regression test.
- Full-location check (2026-11-10): for all 7 violations of the UI run on the Word-saved file, page, section heading, paragraph position in section (non-empty body paragraphs since the heading) and table index + row were compared with values read from Microsoft Word itself (hidden instance, read-only). 23/23 fields match, including the paragraph after an empty page-break paragraph (6), the long-table row (table 1, row 61) and the merged signature cell (table 2, row 1). Pinned as `test_full_locations_match_what_word_reports`.

### Unsupported uploads (added 2026-11-10)

| Layer | Case | Result |
|---|---|---|
| Live API (curl, bypassing the UI) | .pdf, .exe, .csv, no extension, legacy .doc | 415 "Unsupported file type '<ext>'. Supported: .docx, .txt." |
| Live API | PDF renamed to .docx, 0-byte .docx | 422 "not a readable DOCX document" |
| Live API | non-UTF-8 .txt / whitespace-only .txt | 422 "not valid UTF-8" / "no text to check" |
| Live API | 21 MB file | 413 "larger than 20 MB" |
| All of the above | side effects | no history entry, no Gemini call, backend stays healthy |
| Browser (Chrome, real stack) | .pdf pushed into the file input (bypassing the picker filter) | inline "Unsupported file type", Run check disabled, no request |
| Browser | PDF renamed to .docx | backend 422 shown as toast + inline alert, form stays usable, no navigation |
| Full-stack E2E | both browser cases | `src/test/backend/unsupported-uploads.spec.ts`, 2 passed (backend project now 4 passing) |
