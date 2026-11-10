from __future__ import annotations

import pytest
from sqlmodel import Session

from doc_checker.repository.check_run_repository import CheckRunRepository
from doc_checker.repository.db_models import CheckRunRecord
from doc_checker.repository.repository_errors import RecordNotFoundError


@pytest.fixture
def runs(session: Session) -> CheckRunRepository:
    return CheckRunRepository(session)


def add_run(runs: CheckRunRepository, name: str) -> CheckRunRecord:
    return runs.add(
        document_name=name,
        document_sha256="abc",
        document_size_bytes=10,
        status="completed",
        violation_count=1,
        models_used=["primary"],
        rules_snapshot=[{"rule_id": "R1", "title": "T", "text": "Rule."}],
        result={"document_name": name},
        duration_ms=5,
    )


def test_add_and_get_round_trip_json_fields(runs: CheckRunRepository) -> None:
    run = add_run(runs, "a.docx")

    fetched = runs.get(run.id or 0)

    assert fetched.document_name == "a.docx"
    assert fetched.models_used == ["primary"]
    assert fetched.rules_snapshot == [{"rule_id": "R1", "title": "T", "text": "Rule."}]
    assert fetched.result == {"document_name": "a.docx"}


def test_list_is_newest_first_with_paging(runs: CheckRunRepository) -> None:
    for name in ("first", "second", "third"):
        add_run(runs, name)

    assert [run.document_name for run in runs.list_recent(limit=10)] == ["third", "second", "first"]
    assert [run.document_name for run in runs.list_recent(limit=1, offset=1)] == ["second"]


def test_delete_removes_the_run(runs: CheckRunRepository) -> None:
    run = add_run(runs, "a.docx")

    runs.delete(run.id or 0)

    with pytest.raises(RecordNotFoundError):
        runs.get(run.id or 0)


@pytest.mark.parametrize("action", ["get", "delete"])
def test_missing_run_raises_not_found(runs: CheckRunRepository, action: str) -> None:
    with pytest.raises(RecordNotFoundError):
        getattr(runs, action)(999)
