from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok_and_configured_models(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "llm_model": "test-primary-model",
        "llm_fallback_model": "test-fallback-model",
    }


def test_health_never_exposes_api_key(client: TestClient) -> None:
    assert "test-key-not-real" not in client.get("/api/health").text
