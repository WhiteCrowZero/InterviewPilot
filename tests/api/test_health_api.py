from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX


def test_health_check_returns_ok(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
