from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from doc_checker.custom_types.document_types import Block, DocumentFormat
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.custom_types.violation_types import VerifiedViolation


class CheckStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ChunkFailureReason(StrEnum):
    QUOTA_EXCEEDED = "quota_exceeded"
    OVERLOADED = "overloaded"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    INVALID_RESPONSE = "invalid_response"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class FailedChunk:
    chunk_id: str
    first_block_id: str
    last_block_id: str
    reason: ChunkFailureReason
    message: str


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one check run. `context_blocks` are the blocks the violations point into."""

    document_name: str
    document_format: DocumentFormat
    status: CheckStatus
    rules: tuple[CheckRule, ...]
    violations: tuple[VerifiedViolation, ...]
    context_blocks: tuple[Block, ...]
    block_count: int
    chunks_total: int
    failed_chunks: tuple[FailedChunk, ...]
    dropped_count: int
    models_used: tuple[str, ...]
    fallback_chunk_count: int
    has_page_layout: bool
    duration_ms: int
