from spec.factories import UserFactory


def test_update_user(client, auth_headers, db_session):
    user = UserFactory(first_name="Old")

    response = client.put(
        f"/users/{user.id}",
        headers=auth_headers,
        json={"first_name": "Updated"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"
