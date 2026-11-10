from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from doc_checker.constants import RULE_TITLE_MAX_LENGTH
from doc_checker.repository.default_rules import DEFAULT_RULES


def test_list_returns_seeded_rules(client: TestClient) -> None:
    response = client.get("/api/rules")

    assert response.status_code == 200
    body = response.json()
    assert [rule["title"] for rule in body] == [title for title, _ in DEFAULT_RULES]
    assert set(body[0]) == {"id", "title", "text", "is_active", "created_at", "updated_at"}
    assert body[0]["created_at"].endswith(("Z", "+00:00"))


def test_create_returns_201_and_the_rule(client: TestClient) -> None:
    response = client.post("/api/rules", json={"title": "  No dates ", "text": "No dates."})

    assert response.status_code == 201
    assert response.json()["title"] == "No dates"
    assert response.json()["is_active"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "text": "x"},
        {"title": "x", "text": "   "},
        {"title": "x" * (RULE_TITLE_MAX_LENGTH + 1), "text": "x"},
        {"title": "x"},
        {"title": "x", "text": "y", "unexpected": 1},
    ],
)
def test_create_rejects_invalid_payloads(client: TestClient, payload: dict[str, object]) -> None:
    assert client.post("/api/rules", json=payload).status_code == 422


def test_patch_updates_only_given_fields(client: TestClient) -> None:
    rule_id = client.get("/api/rules").json()[0]["id"]

    response = client.patch(f"/api/rules/{rule_id}", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["title"] == DEFAULT_RULES[0][0]


def test_patch_with_empty_body_is_rejected(client: TestClient) -> None:
    rule_id = client.get("/api/rules").json()[0]["id"]

    assert client.patch(f"/api/rules/{rule_id}", json={}).status_code == 422


def test_active_filter_excludes_inactive_rules(client: TestClient) -> None:
    rule_id = client.get("/api/rules").json()[0]["id"]
    client.patch(f"/api/rules/{rule_id}", json={"is_active": False})

    active_ids = [rule["id"] for rule in client.get("/api/rules?active=true").json()]

    assert rule_id not in active_ids
    assert len(active_ids) == len(DEFAULT_RULES) - 1


def test_delete_returns_204_and_the_rule_is_gone(client: TestClient) -> None:
    rule_id = client.get("/api/rules").json()[0]["id"]

    assert client.delete(f"/api/rules/{rule_id}").status_code == 204
    assert rule_id not in [rule["id"] for rule in client.get("/api/rules").json()]


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_missing_rule_returns_404_with_detail(client: TestClient, method: str) -> None:
    if method == "patch":
        response = client.patch("/api/rules/999", json={"title": "x"})
    else:
        response = client.delete("/api/rules/999")

    assert response.status_code == 404
    assert "999" in response.json()["detail"]
