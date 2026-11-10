from __future__ import annotations

APPLICATION_NAME = "doc-checker"
APP_TITLE = "Document Rule Compliance Checker"

API_PREFIX = "/api"
HEALTH_PATH = "/health"
HEALTH_STATUS_OK = "ok"

BLOCK_ID_PREFIX = "B"
TABLE_CELL_SEPARATOR = " | "
TXT_ENCODING = "utf-8-sig"

DOCX_HEADING_STYLE_PREFIX = "Heading "
DOCX_TITLE_STYLE_NAME = "Title"
DOCX_LIST_STYLE_PREFIX = "List"

CHUNK_ID_PREFIX = "C"
CHARS_PER_TOKEN_ESTIMATE = 4
HEADING_PATH_SEPARATOR = " > "

# One-to-one character equivalences, so offsets in the canonical text equal offsets in the original.
QUOTE_CHAR_EQUIVALENTS = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    " ": " ",
}
QUOTE_WRAPPER_CHARS = "\"'‘’“” "

RULE_ID_PREFIX = "R"
LLM_RESPONSE_MIME_TYPE = "application/json"
LLM_REQUEST_TIMEOUT_MS = 60_000
LLM_HTTP_RETRY_ATTEMPTS = 3
LLM_RETRYABLE_HTTP_STATUS_CODES = (500, 502, 503, 504)
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_SERVICE_UNAVAILABLE = 503

RULES_PATH = "/rules"
CHECKS_PATH = "/checks"
RULE_TITLE_MAX_LENGTH = 200
RULE_TEXT_MAX_LENGTH = 2000
HISTORY_DEFAULT_PAGE_SIZE = 50
HISTORY_MAX_PAGE_SIZE = 200
BYTES_PER_MEGABYTE = 1024 * 1024
SQLITE_MEMORY_DATABASE = ":memory:"
