from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from doc_checker.constants import RULE_TEXT_MAX_LENGTH, RULE_TITLE_MAX_LENGTH
from doc_checker.custom_types.check_types import CheckStatus, ChunkFailureReason
from doc_checker.custom_types.document_types import BlockKind, DocumentFormat
from doc_checker.custom_types.violation_types import Severity


def _as_utc(value: datetime) -> datetime:
    """SQLite drops the timezone; stored values are UTC, so re-attach it."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]
RuleTitle = Annotated[str, Field(min_length=1, max_length=RULE_TITLE_MAX_LENGTH)]
RuleText = Annotated[str, Field(min_length=1, max_length=RULE_TEXT_MAX_LENGTH)]


class RuleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: RuleTitle
    text: RuleText
    is_active: bool = True


class RuleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: RuleTitle | None = None
    text: RuleText | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _require_a_change(self) -> Self:
        if self.title is None and self.text is None and self.is_active is None:
            raise ValueError("Provide at least one of: title, text, is_active.")
        return self


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    text: str
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime


class CheckRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    title: str
    text: str


class ViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    block_id: str
    quote: str
    start: int
    end: int
    explanation: str
    severity: Severity


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    block_id: str
    index: int
    kind: BlockKind
    text: str
    heading_path: list[str]
    # Defaults keep history saved before these fields existed readable.
    section_position: int | None = None
    table_number: int | None = None
    table_row: int | None = None
    page: int | None = None


class FailedChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    first_block_id: str
    last_block_id: str
    reason: ChunkFailureReason
    message: str


class CheckResultResponse(BaseModel):
    """Serialized `CheckResult`; also the exact JSON stored in check history."""

    model_config = ConfigDict(from_attributes=True)

    document_name: str
    document_format: DocumentFormat
    status: CheckStatus
    rules: list[CheckRuleResponse]
    violations: list[ViolationResponse]
    context_blocks: list[BlockResponse]
    block_count: int
    chunks_total: int
    failed_chunks: list[FailedChunkResponse]
    dropped_count: int
    models_used: list[str]
    # None only for history saved before this field existed: unknown, not zero.
    fallback_chunk_count: int | None = None
    # None only for history saved before page support: unknown, not "no layout".
    has_page_layout: bool | None = None
    duration_ms: int


class CheckRunResponse(BaseModel):
    id: int
    created_at: UtcDatetime
    document_sha256: str
    document_size_bytes: int
    result: CheckResultResponse


class CheckRunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: UtcDatetime
    document_name: str
    status: CheckStatus
    violation_count: int
    models_used: list[str]
