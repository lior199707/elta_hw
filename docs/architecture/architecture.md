# Architecture

Diagrams are Mermaid (rendered by GitHub; paste any block into https://mermaid.live to edit) and
DBML for the ERD (`erd.dbml`, paste into https://dbdiagram.io). Every name below is a real module,
function or endpoint in this repository.

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Check Request, End to End](#2-check-request-end-to-end)
3. [LLM Call with Fallback](#3-llm-call-with-fallback)
4. [Document Processing Pipeline](#4-document-processing-pipeline)
5. [Data Model (ERD)](#5-data-model-erd)
6. [Frontend Structure](#6-frontend-structure)
7. [Agent Skill Flow](#7-agent-skill-flow)

---

## 1. System Overview

```mermaid
flowchart LR
    user([User]) --> browser["Browser: React app<br/>Check, Rules, History pages"]
    browser -->|"HTTP /api/*"| nginx["nginx (frontend container, :8080)<br/>serves SPA, proxies /api"]
    nginx --> api["FastAPI backend (:8000)<br/>doc_checker.main:build_app"]
    api --> db[("SQLite<br/>Docker volume backend-data<br/>/data/doc_checker.db")]
    api -->|"google-genai SDK"| gemini[("Gemini API<br/>primary + fallback model")]
    env[".env<br/>GEMINI_API_KEY, LLM_MODEL,<br/>LLM_FALLBACK_MODEL, ..."] -.->|load_config| api
    agent([AI agent, e.g. Claude Code]) --> skill["Agent Skill<br/>skills/document-rules-check"]
    skill -.->|"same extraction logic,<br/>no API key"| docs[(".docx / .txt file")]
```

| Component | Location | Responsibility |
|---|---|---|
| Frontend | `frontend/src` (features `rules`, `checks`) | Rules console, upload, results view (sort, filters, location chips), history |
| nginx | `frontend/nginx.conf` | Static files, `/api` proxy, 25 MB body limit, 600 s read timeout |
| API | `backend/src/doc_checker/api` | `health`, `rules` (CRUD), `checks` (upload, history) routers; domain errors to HTTP codes |
| Service | `services/compliance_checker.py` | Orchestrates one check |
| Persistence | `repository/` | SQLModel tables, seeding, repositories |
| Agent Skill | `skills/document-rules-check` | Same check inside an AI agent, scripts for the deterministic parts |

---

## 2. Check Request, End to End

`POST /api/checks` (`api/checks_router.py: create_check`):

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant UI as CheckPage (React)
    participant R as checks_router.create_check
    participant RR as RuleRepository
    participant S as ComplianceChecker.check
    participant L as GeminiLlmClient
    participant V as verify_violations
    participant CR as CheckRunRepository

    U->>UI: choose .docx/.txt, tick rules, Run check
    UI->>UI: validateDocumentFile (extension, 20 MB)
    UI->>R: multipart file + rule_ids
    R->>R: read at most MAX_UPLOAD_MB + 1 bytes
    alt file too large
        R-->>UI: 413 FileTooLargeError
    end
    R->>RR: get_many(rule_ids) or list_rules(active_only=True)
    alt unknown rule id
        RR-->>UI: 404 RecordNotFoundError
    end
    R->>S: check(filename, content, rules as CheckRule with ids R + rule.id)
    alt no rules
        S-->>UI: 422 NoRulesSelectedError
    end
    S->>S: extract_document (415 unsupported, 422 unreadable or empty)
    S->>S: build_chunks(blocks, CHUNK_TOKEN_BUDGET, CHUNK_OVERLAP_BLOCKS)
    par every chunk, at most LLM_MAX_CONCURRENCY at once
        S->>L: find_violations(rules, chunk)
        L-->>S: LlmCheckOutcome or LlmError (chunk recorded as failed)
    end
    S->>V: verify_violations(all candidates, document, rule ids)
    V-->>S: verified violations + dropped
    S-->>R: CheckResult (status completed / partial / failed)
    R->>CR: add(... rules_snapshot, result JSON ...)
    R-->>UI: 201 CheckRunResponse
    UI->>U: navigate to /history/:id (result view)
```

Model failures never become "no violations": a failed chunk makes the run `partial` (or `failed`
when every chunk failed) and the run is still stored, so it appears in history with the reason.

---

## 3. LLM Call with Fallback

`llm/gemini_client.py: GeminiLlmClient.find_violations` (one call per chunk):

```mermaid
flowchart TD
    start["find_violations(rules, chunk)"] --> prompt["build_user_prompt:<br/>&lt;rules&gt; R1..Rn &lt;/rules&gt;<br/>&lt;document&gt; [B12] (location) text &lt;/document&gt;"]
    prompt --> primary["generate_content(LLM_MODEL)<br/>system instruction + JSON schema LlmViolationReport<br/>SDK retries 500/502/503/504"]
    primary -->|"429 quota / 503 overload / timeout"| fallback["generate_content(LLM_FALLBACK_MODEL)<br/>used_fallback = True"]
    primary -->|"other HTTP error or network error"| unavailable["LlmUnavailableError"]
    primary -->|answer| parse
    fallback -->|answer| parse
    fallback -->|"capacity error again"| capacity["LlmQuotaExceededError /<br/>LlmOverloadedError / LlmTimeoutError"]
    parse{"blocked? truncated?<br/>schema valid?"} -->|"prompt or answer blocked"| blocked["LlmBlockedError"]
    parse -->|"MAX_TOKENS or invalid JSON"| invalid["LlmResponseError"]
    parse -->|ok| outcome["LlmCheckOutcome<br/>(candidates, model_used, used_fallback)"]
    unavailable --> failed["ComplianceChecker records FailedChunk<br/>reason: quota_exceeded | overloaded | timeout |<br/>blocked | invalid_response | unavailable"]
    capacity --> failed
    blocked --> failed
    invalid --> failed
```

---

## 4. Document Processing Pipeline

```mermaid
flowchart LR
    file[".docx / .txt bytes"] --> fmt{"extension"}
    fmt -->|".docx"| docx["DocxExtractor<br/>iter_inner_content: paragraphs + tables in order<br/>headings, list items, merged cells,<br/>headers/footers, _PageTracker"]
    fmt -->|".txt"| txt["TxtExtractor<br/>UTF-8, split on blank lines"]
    fmt -->|other| e415["415 UnsupportedDocumentTypeError"]
    docx --> norm["_build_blocks<br/>normalize whitespace, drop empty,<br/>number B1..Bn"]
    txt --> norm
    norm --> blocks["Block: id, kind, text, heading_path,<br/>page, section_position, table_number, table_row"]
    blocks --> chunks["build_chunks<br/>token budget, overlap 2 blocks,<br/>oversized block alone"]
    chunks --> llm["LLM per chunk"]
    llm --> verify["verify_violations<br/>quote must be verbatim (tolerant of<br/>whitespace, quote style, dashes, case),<br/>fix block id, dedupe overlap,<br/>drop contained spans"]
    verify --> result["CheckResult<br/>violations + context_blocks"]
```

Locations shown to the user come only from facts in the file: section (nearest heading), paragraph
or list-item number among non-empty paragraphs in that section, table number and row as Word counts
them, and the page where the block starts in the layout Microsoft Word saved
(`w:lastRenderedPageBreak`). Files without a saved layout show no page numbers.

---

## 5. Data Model (ERD)

Rendered from `erd.dbml` on dbdiagram.io (no line between the tables: there is no foreign key,
see the note below):

![ERD rendered by dbdiagram.io](DB.png)

The same model in Mermaid, with the logical (not enforced) relationship drawn as a dotted line:

```mermaid
erDiagram
    rule {
        INTEGER id PK
        VARCHAR title "1 to 200 chars"
        VARCHAR text "1 to 2000 chars"
        BOOLEAN is_active "default true"
        DATETIME created_at "UTC"
        DATETIME updated_at "UTC"
    }
    check_run {
        INTEGER id PK
        VARCHAR document_name
        VARCHAR document_sha256 "document itself not stored"
        INTEGER document_size_bytes
        VARCHAR status "completed | partial | failed"
        INTEGER violation_count
        JSON models_used
        JSON rules_snapshot "copy of rules at run time"
        JSON result "full CheckResult"
        INTEGER duration_ms
        DATETIME created_at "indexed, UTC"
    }
    rule ||..o{ check_run : "copied into rules_snapshot (no FK)"
```

The dotted line is logical only: there is no foreign key, by design. A run keeps its own copy of
the rules (`rule_id` = `"R" + rule.id`), so history stays correct after rules are edited or deleted.

---

## 6. Frontend Structure

```mermaid
flowchart TD
    main["main.tsx"] --> providers["AppProviders<br/>QueryClientProvider + Toaster"]
    providers --> router["createBrowserRouter (app/router)"]
    router --> check["/ CheckPage"]
    router --> rules["/rules RulesPage"]
    router --> history["/history HistoryPage"]
    router --> detail["/history/:id CheckResultPage"]
    check --> checkForm["features/checks: CheckForm<br/>FileDropzone, RuleSelector"]
    rules --> rulesManager["features/rules: RulesManager<br/>RuleFormDialog, ConfirmDialog"]
    history --> historyList["features/checks: HistoryList"]
    detail --> resultView["CheckResultView<br/>ResultSummary, CoverageWarning, FallbackNotice,<br/>ResultSortControl, ResultFilters (URL state),<br/>ViolationCard + LocationChips"]
    checkForm --> hooks["hooks: useChecks / useRules<br/>TanStack Query + key factories"]
    rulesManager --> hooks
    historyList --> hooks
    resultView --> hooks
    hooks --> repos["api/repository.ts<br/>Zod-validated responses"]
    repos --> http["lib/api/httpClient<br/>parses {detail} errors"]
    http -->|"/api"| backend[("FastAPI")]
```

---

## 7. Agent Skill Flow

```mermaid
flowchart TD
    a1["1. uv run --quiet scripts/extract.py file<br/>validate type, size, corrupt, empty"] -->|"ok=false (exit 2-5)"| stop["Tell the user why, stop"]
    a1 -->|ok| ws["workspace: blocks.json + chunks/chunk-NNN.txt"]
    ws --> a2["2. Agent writes rules.json from the user's rules<br/>verify.py --rules-only, then user confirms"]
    a2 --> a3["3. Agent reads every chunk and writes<br/>findings/chunk-NNN.json (empty list if none)"]
    a3 --> a4["4. verify.py: verbatim quotes, fix block ids,<br/>dedupe, coverage, report.md + report.json"]
    a4 -->|"status partial"| a3
    a4 -->|"status completed"| a5["5. Summary in chat + path to report.md"]
```
