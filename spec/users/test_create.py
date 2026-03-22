def test_create_user(client, auth_headers):
    response = client.post(
        "/users",
        headers=auth_headers,
        json={
            "email": "new-user@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "password",
            "password_confirmation": "password",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new-user@example.com"
