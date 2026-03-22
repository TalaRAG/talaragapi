def test_users_requires_authentication(client):
    response = client.get("/users")

    assert response.status_code == 403
    assert response.json() == {"detail": "authentication required"}
