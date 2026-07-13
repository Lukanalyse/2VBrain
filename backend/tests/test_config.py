from fastapi.testclient import TestClient

from main import create_app


def test_config_contract() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/config")

    assert response.status_code == 200
    assert set(response.json()) == {
        "vault_path",
        "library_path",
        "llm_provider",
        "vector_store_provider",
    }
