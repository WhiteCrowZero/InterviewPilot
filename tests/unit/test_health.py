from tests.conftest import create_test_client


def test_health_check() -> None:
    client = create_test_client()
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
