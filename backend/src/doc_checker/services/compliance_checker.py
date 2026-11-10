from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from doc_checker.chunking.block_chunker import build_chunks
from doc_checker.custom_types.check_types import (
    CheckResult,
    CheckStatus,
    ChunkFailureReason,
    FailedChunk,
)
from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.document_types import Block, ExtractedDocument
from doc_checker.custom_types.llm_types import LlmCheckOutcome
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.custom_types.violation_types import VerifiedViolation
from doc_checker.extraction.document_extraction import extract_document
from doc_checker.llm.llm_client import LlmClient
from doc_checker.llm.llm_errors import (
    LlmBlockedError,
    LlmError,
    LlmOverloadedError,
    LlmQuotaExceededError,
    LlmResponseError,
    LlmTimeoutError,
)
from doc_checker.verification.quote_verifier import verify_violations

logger = logging.getLogger(__name__)

# Subclasses before their base (LlmOverloadedError and LlmTimeoutError extend LlmUnavailableError).
_FAILURE_REASONS: tuple[tuple[type[LlmError], ChunkFailureReason], ...] = (
    (LlmQuotaExceededError, ChunkFailureReason.QUOTA_EXCEEDED),
    (LlmOverloadedError, ChunkFailureReason.OVERLOADED),
    (LlmTimeoutError, ChunkFailureReason.TIMEOUT),
    (LlmBlockedError, ChunkFailureReason.BLOCKED),
    (LlmResponseError, ChunkFailureReason.INVALID_RESPONSE),
)


class CheckError(Exception):
    """Base for check-level failures that are not extraction or LLM errors."""


class NoRulesSelectedError(CheckError):
    """A check was requested without any rule to check against."""


@dataclass(frozen=True)
class _ChunkOutcome:
    chunk: Chunk
    outcome: LlmCheckOutcome | None
    failure: FailedChunk | None


class ComplianceChecker:
    def __init__(
        self, llm: LlmClient, token_budget: int, overlap_blocks: int, max_concurrency: int
    ) -> None:
        self._llm = llm
        self._token_budget = token_budget
        self._overlap_blocks = overlap_blocks
        self._max_concurrency = max_concurrency

    async def check(self, filename: str, content: bytes, rules: Sequence[CheckRule]) -> CheckResult:
        """Extract, chunk, ask the model per chunk (bounded concurrency), verify, and merge.

        A chunk whose LLM call fails is recorded in `failed_chunks` (status PARTIAL, or FAILED
        when no chunk succeeded); it is never reported as clean. Raises NoRulesSelectedError,
        and lets ExtractionError subtypes and unexpected exceptions propagate.
        """
        if not rules:
            raise NoRulesSelectedError("Select at least one rule to check the document against.")

        started = time.monotonic()
        document = extract_document(filename, content)
        chunks = build_chunks(document.blocks, self._token_budget, self._overlap_blocks)
        outcomes = await self._check_chunks(rules, chunks)

        succeeded = [item.outcome for item in outcomes if item.outcome is not None]
        failed = tuple(item.failure for item in outcomes if item.failure is not None)
        candidates = [candidate for outcome in succeeded for candidate in outcome.candidates]
        verification = verify_violations(candidates, document, {rule.rule_id for rule in rules})

        result = CheckResult(
            document_name=filename,
            document_format=document.document_format,
            status=_status(chunk_count=len(chunks), failed_count=len(failed)),
            rules=tuple(rules),
            violations=verification.violations,
            context_blocks=_context_blocks(document, verification.violations),
            block_count=len(document.blocks),
            chunks_total=len(chunks),
            failed_chunks=failed,
            dropped_count=len(verification.dropped),
            models_used=tuple(sorted({outcome.model_used for outcome in succeeded})),
            fallback_chunk_count=sum(outcome.used_fallback for outcome in succeeded),
            has_page_layout=any(block.page is not None for block in document.blocks),
            duration_ms=round((time.monotonic() - started) * 1000),
        )
        logger.info(
            "check finished",
            extra={
                "status": result.status,
                "rule_count": len(rules),
                "chunk_count": result.chunks_total,
                "failed_chunk_count": len(failed),
                "violation_count": len(result.violations),
                "dropped_count": result.dropped_count,
                "duration_ms": result.duration_ms,
            },
        )
        return result

    async def _check_chunks(
        self, rules: Sequence[CheckRule], chunks: Sequence[Chunk]
    ) -> list[_ChunkOutcome]:
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def check_one(chunk: Chunk) -> _ChunkOutcome:
            async with semaphore:
                try:
                    outcome = await self._llm.find_violations(rules, chunk)
                except LlmError as exc:
                    logger.warning(
                        "chunk check failed",
                        extra={"chunk_id": chunk.chunk_id, "error_type": type(exc).__name__},
                    )
                    return _ChunkOutcome(chunk, None, _failed_chunk(chunk, exc))
                return _ChunkOutcome(chunk, outcome, None)

        # TaskGroup cancels the remaining chunks if an unexpected (non-LLM) exception escapes.
        try:
            async with asyncio.TaskGroup() as group:
                tasks = [group.create_task(check_one(chunk)) for chunk in chunks]
        except ExceptionGroup as errors:
            # Surface the original error type to callers; the group stays attached as the cause.
            raise errors.exceptions[0] from errors
        return [task.result() for task in tasks]


def _failed_chunk(chunk: Chunk, error: LlmError) -> FailedChunk:
    reason = next(
        (reason for error_type, reason in _FAILURE_REASONS if isinstance(error, error_type)),
        ChunkFailureReason.UNAVAILABLE,
    )
    return FailedChunk(
        chunk_id=chunk.chunk_id,
        first_block_id=chunk.blocks[0].block_id,
        last_block_id=chunk.blocks[-1].block_id,
        reason=reason,
        message=str(error),
    )


def _status(chunk_count: int, failed_count: int) -> CheckStatus:
    if failed_count == 0:
        return CheckStatus.COMPLETED
    if failed_count == chunk_count:
        return CheckStatus.FAILED
    return CheckStatus.PARTIAL


def _context_blocks(
    document: ExtractedDocument, violations: Sequence[VerifiedViolation]
) -> tuple[Block, ...]:
    referenced = {violation.block_id for violation in violations}
    return tuple(block for block in document.blocks if block.block_id in referenced)
