def test_environment_requires_admin_user(client, auth_headers):
    response = client.get("/system/environment", headers=auth_headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "admin required"}


def test_environment_returns_backend_variables_for_admin(client, admin_auth_headers):
    response = client.get("/system/environment", headers=admin_auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["variables"]["INFERENCE_PROVIDER"] == "openai"
    assert "DOCUMENT_TYPES" in payload["variables"]
