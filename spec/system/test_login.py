from spec.factories import UserFactory


def test_login_returns_token(client, db_session):
    user = UserFactory(email="admin@example.com")

    response = client.post(
        "/login",
        json={"email": user.email, "password": "password"},
    )

    assert response.status_code == 200
    assert "token" in response.json()
