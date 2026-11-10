"""Rules lifecycle through the API, checking the effect on what a check sends to the model."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.fakes import FakeLlm

DOCUMENT = b"Intro.\n\nRange is 50 km."


def run_check(client: TestClient, rule_ids: list[int] | None = None) -> int:
    data = {"rule_ids": [str(rule_id) for rule_id in rule_ids]} if rule_ids else None
    response = client.post("/api/checks", files={"file": ("doc.txt", DOCUMENT)}, data=data)
    return response.status_code


def last_sent_rule_ids(fake_llm: FakeLlm) -> list[str]:
    return [rule.rule_id for rule in fake_llm.calls[-1][0]]


def active_ids(client: TestClient) -> list[int]:
    return [rule["id"] for rule in client.get("/api/rules?active=true").json()]


def all_ids(client: TestClient) -> list[int]:
    return [rule["id"] for rule in client.get("/api/rules").json()]


def test_add_deactivate_reactivate_delete_drives_what_checks_use(
    client: TestClient, fake_llm: FakeLlm
) -> None:
    created = client.post("/api/rules", json={"title": "No dates", "text": "No dates."}).json()
    rule_id, prompt_id = created["id"], f"R{created['id']}"

    assert rule_id in active_ids(client)
    assert run_check(client) == 201
    assert prompt_id in last_sent_rule_ids(fake_llm)

    client.patch(f"/api/rules/{rule_id}", json={"is_active": False})
    assert rule_id not in active_ids(client)
    assert rule_id in all_ids(client)
    assert run_check(client) == 201
    assert prompt_id not in last_sent_rule_ids(fake_llm)
    assert run_check(client, rule_ids=[rule_id]) == 201
    assert last_sent_rule_ids(fake_llm) == [prompt_id]

    client.patch(f"/api/rules/{rule_id}", json={"is_active": True})
    assert rule_id in active_ids(client)
    assert run_check(client) == 201
    assert prompt_id in last_sent_rule_ids(fake_llm)

    first_run_id = client.get("/api/checks").json()[-1]["id"]
    assert client.delete(f"/api/rules/{rule_id}").status_code == 204
    assert rule_id not in all_ids(client)
    calls_before = len(fake_llm.calls)
    assert run_check(client, rule_ids=[rule_id]) == 404
    assert len(fake_llm.calls) == calls_before

    snapshot = client.get(f"/api/checks/{first_run_id}").json()["result"]["rules"]
    assert prompt_id in [rule["rule_id"] for rule in snapshot]
