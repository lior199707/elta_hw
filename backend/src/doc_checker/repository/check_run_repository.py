from __future__ import annotations

from typing import Any

from sqlmodel import Session, col, select

from doc_checker.repository.db_models import CheckRunRecord
from doc_checker.repository.repository_errors import RecordNotFoundError


class CheckRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        document_name: str,
        document_sha256: str,
        document_size_bytes: int,
        status: str,
        violation_count: int,
        models_used: list[str],
        rules_snapshot: list[dict[str, Any]],
        result: dict[str, Any],
        duration_ms: int,
    ) -> CheckRunRecord:
        run = CheckRunRecord(
            document_name=document_name,
            document_sha256=document_sha256,
            document_size_bytes=document_size_bytes,
            status=status,
            violation_count=violation_count,
            models_used=models_used,
            rules_snapshot=rules_snapshot,
            result=result,
            duration_ms=duration_ms,
        )
        self._session.add(run)
        self._session.commit()
        self._session.refresh(run)
        return run

    def list_recent(self, limit: int, offset: int = 0) -> list[CheckRunRecord]:
        """Newest first."""
        statement = (
            select(CheckRunRecord)
            # The id breaks ties between runs stored within the same clock tick.
            .order_by(col(CheckRunRecord.created_at).desc(), col(CheckRunRecord.id).desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.exec(statement).all())

    def get(self, run_id: int) -> CheckRunRecord:
        """Raises RecordNotFoundError."""
        run = self._session.get(CheckRunRecord, run_id)
        if run is None:
            raise RecordNotFoundError(f"Check run {run_id} does not exist.")
        return run

    def delete(self, run_id: int) -> None:
        """Raises RecordNotFoundError."""
        self._session.delete(self.get(run_id))
        self._session.commit()
