from fastapi.testclient import TestClient

from main import create_app


def test_health_check() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_rejects_untrusted_browser_origins() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/assistant/config",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_local_frontend_origin() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/v1/assistant/config",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
