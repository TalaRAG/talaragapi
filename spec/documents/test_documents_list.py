def test_list_documents_returns_paginated_records(client, auth_headers, document):
    response = client.get("/documents", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_page"] == 1
    assert payload["total_pages"] == 1
    assert payload["records"][0]["id"] == document.id
    assert payload["records"][0]["status"] == document.status
