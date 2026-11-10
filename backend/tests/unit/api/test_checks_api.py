from __future__ import annotations

import hashlib

import httpx2
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session

from doc_checker.config import AppConfig
from doc_checker.constants import BYTES_PER_MEGABYTE
from doc_checker.llm.llm_errors import LlmQuotaExceededError
from doc_checker.main import create_app
from doc_checker.repository.database import create_db_engine
from doc_checker.repository.db_models import CheckRunRecord
from tests.fakes import FakeLlm

LOCATION_KEYS = {"section_position", "table_number", "table_row"}

DOCUMENT = b"Intro.\n\nRange is 50 km.\n\nSpeed is Mach 2."


def upload(
    client: TestClient,
    content: bytes = DOCUMENT,
    filename: str = "spec.txt",
    rule_ids: list[int] | None = None,
) -> httpx2.Response:
    data = {"rule_ids": [str(rule_id) for rule_id in rule_ids]} if rule_ids else None
    return client.post("/api/checks", files={"file": (filename, content)}, data=data)


def active_rule_ids(client: TestClient) -> list[int]:
    return [rule["id"] for rule in client.get("/api/rules?active=true").json()]


def test_check_runs_against_active_rules_and_persists(
    client: TestClient, fake_llm: FakeLlm
) -> None:
    response = upload(client)

    assert response.status_code == 201
    body = response.json()
    assert body["document_sha256"] == hashlib.sha256(DOCUMENT).hexdigest()
    assert body["document_size_bytes"] == len(DOCUMENT)
    result = body["result"]
    assert result["status"] == "completed"
    assert [v["quote"] for v in result["violations"]] == ["50 km", "Mach 2"]
    assert [b["block_id"] for b in result["context_blocks"]] == ["B2", "B3"]
    assert [r["rule_id"] for r in result["rules"]] == [f"R{i}" for i in active_rule_ids(client)]
    sent_rule_ids = [rule.rule_id for rule in fake_llm.calls[0][0]]
    assert sent_rule_ids == [f"R{i}" for i in active_rule_ids(client)]
    assert client.get(f"/api/checks/{body['id']}").json() == body


def test_inactive_rules_are_not_sent(client: TestClient, fake_llm: FakeLlm) -> None:
    first_id = active_rule_ids(client)[0]
    client.patch(f"/api/rules/{first_id}", json={"is_active": False})

    upload(client)

    assert f"R{first_id}" not in [rule.rule_id for rule in fake_llm.calls[0][0]]


def test_explicit_rule_ids_select_exactly_those_rules(
    client: TestClient, fake_llm: FakeLlm
) -> None:
    chosen = active_rule_ids(client)[1]

    response = upload(client, rule_ids=[chosen])

    assert response.status_code == 201
    assert [rule.rule_id for rule in fake_llm.calls[0][0]] == [f"R{chosen}"]


def test_unknown_rule_id_returns_404(client: TestClient, fake_llm: FakeLlm) -> None:
    response = upload(client, rule_ids=[999])

    assert response.status_code == 404
    assert "999" in response.json()["detail"]
    assert fake_llm.calls == []


def test_no_active_rules_returns_422(client: TestClient, fake_llm: FakeLlm) -> None:
    for rule_id in active_rule_ids(client):
        client.patch(f"/api/rules/{rule_id}", json={"is_active": False})

    response = upload(client)

    assert response.status_code == 422
    assert fake_llm.calls == []


def test_unsupported_file_type_returns_415(client: TestClient) -> None:
    response = upload(client, filename="spec.pdf")

    assert response.status_code == 415
    assert ".docx" in response.json()["detail"]


def test_corrupt_docx_returns_422(client: TestClient) -> None:
    assert upload(client, content=b"not a docx", filename="spec.docx").status_code == 422


def test_document_without_text_returns_422(client: TestClient) -> None:
    assert upload(client, content=b"   \n\n  ").status_code == 422


def test_file_over_the_size_limit_returns_413(app_config: AppConfig) -> None:
    config = app_config.model_copy(update={"max_upload_mb": 1})
    llm = FakeLlm(lambda chunk: LlmQuotaExceededError("unused"))
    app = create_app(config, llm=llm, engine=create_db_engine("sqlite:///:memory:"))
    with TestClient(app) as client:
        response = upload(client, content=b"x" * (BYTES_PER_MEGABYTE + 1))

    assert response.status_code == 413
    assert llm.calls == []


def test_failed_check_is_still_stored_with_failed_status(app_config: AppConfig) -> None:
    llm = FakeLlm(lambda chunk: LlmQuotaExceededError("quota exhausted"))
    app = create_app(app_config, llm=llm, engine=create_db_engine("sqlite:///:memory:"))
    with TestClient(app) as client:
        response = upload(client)
        history = client.get("/api/checks").json()

    assert response.status_code == 201
    assert response.json()["result"]["status"] == "failed"
    assert response.json()["result"]["failed_chunks"][0]["reason"] == "quota_exceeded"
    assert history[0]["status"] == "failed"


def test_history_lists_runs_newest_first(client: TestClient) -> None:
    first = upload(client, filename="first.txt").json()
    second = upload(client, filename="second.txt").json()

    history = client.get("/api/checks").json()

    assert [run["id"] for run in history] == [second["id"], first["id"]]
    assert history[0] == {
        "id": second["id"],
        "created_at": second["created_at"],
        "document_name": "second.txt",
        "status": "completed",
        "violation_count": 2,
        "models_used": ["primary"],
    }


def test_history_snapshot_survives_rule_edits(client: TestClient) -> None:
    rule_id = active_rule_ids(client)[0]
    run = upload(client).json()
    original_text = run["result"]["rules"][0]["text"]

    client.patch(f"/api/rules/{rule_id}", json={"text": "Completely different text."})

    stored = client.get(f"/api/checks/{run['id']}").json()
    assert stored["result"]["rules"][0]["text"] == original_text


def test_delete_run_then_404(client: TestClient) -> None:
    run_id = upload(client).json()["id"]

    assert client.delete(f"/api/checks/{run_id}").status_code == 204
    assert client.get(f"/api/checks/{run_id}").status_code == 404


def test_result_exposes_block_locations_and_fallback_count(client: TestClient) -> None:
    result = upload(client).json()["result"]

    assert result["fallback_chunk_count"] == 0
    assert result["has_page_layout"] is False
    assert result["context_blocks"][0]["section_position"] == 2
    assert result["context_blocks"][0]["table_number"] is None
    assert result["context_blocks"][0]["table_row"] is None


def test_history_saved_before_new_fields_still_loads(client: TestClient, engine: Engine) -> None:
    run_id = upload(client).json()["id"]
    with Session(engine) as session:
        run = session.get(CheckRunRecord, run_id)
        assert run is not None
        legacy = dict(run.result)
        legacy.pop("fallback_chunk_count")
        legacy.pop("has_page_layout")
        legacy["context_blocks"] = [
            {key: value for key, value in block.items() if key not in LOCATION_KEYS}
            for block in legacy["context_blocks"]
        ]
        run.result = legacy
        session.add(run)
        session.commit()

    response = client.get(f"/api/checks/{run_id}")

    assert response.status_code == 200
    assert response.json()["result"]["fallback_chunk_count"] is None
    assert response.json()["result"]["has_page_layout"] is None
    assert response.json()["result"]["context_blocks"][0]["section_position"] is None


def test_result_blocks_expose_page_field(client: TestClient) -> None:
    result = upload(client).json()["result"]

    assert result["context_blocks"][0]["page"] is None
