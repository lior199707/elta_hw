from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class RuleRecord(SQLModel, table=True):
    __tablename__ = "rule"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    text: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CheckRunRecord(SQLModel, table=True):
    """One persisted check. `rules_snapshot` freezes the rules as they were at run time."""

    __tablename__ = "check_run"

    id: int | None = Field(default=None, primary_key=True)
    document_name: str
    document_sha256: str
    document_size_bytes: int
    status: str
    violation_count: int
    models_used: list[str] = Field(sa_column=Column(JSON, nullable=False))
    rules_snapshot: list[dict[str, Any]] = Field(sa_column=Column(JSON, nullable=False))
    result: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    duration_ms: int
    created_at: datetime = Field(default_factory=utc_now, index=True)
