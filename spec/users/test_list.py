from spec.factories import UserFactory


def test_list_users(client, auth_headers, db_session):
    UserFactory(first_name="Alpha", last_name="Admin")
    UserFactory(first_name="Beta", last_name="Builder")

    response = client.get("/users", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["records"]) >= 2
    assert payload["current_page"] == 1
