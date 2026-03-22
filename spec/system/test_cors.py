def test_documents_preflight_uses_configured_cors_settings(client):
    response = client.options(
        "/documents",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-headers"] == "Accept, Accept-Language, Authorization, Content-Language, Content-Type"
    assert response.headers["access-control-max-age"] == "600"


def test_unhandled_errors_still_include_cors_headers(app, admin_auth_headers, monkeypatch):
    from fastapi.testclient import TestClient

    def raise_runtime_error(self):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.operations.documents.save.Save.execute", raise_runtime_error)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/documents",
        headers={
            **admin_auth_headers,
            "Origin": "http://localhost:8000",
        },
        data={
            "name": "Broken upload",
            "document_type": "national_budget",
        },
        files={
            "file": ("broken.txt", b"hello", "text/plain"),
        },
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"
    assert response.headers["access-control-allow-credentials"] == "true"
