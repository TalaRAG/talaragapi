def test_update_document_without_replacing_file(client, auth_headers, document):
    response = client.put(
        f"/documents/{document.id}",
        headers=auth_headers,
        data={
            "name": "Updated Document Name",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Updated Document Name"
    assert payload["description"] == "Updated description"
    assert payload["status"] == document.status
    assert payload["original_filename"] == document.original_filename


def test_update_document_status(client, auth_headers, document):
    response = client.put(
        f"/documents/{document.id}",
        headers=auth_headers,
        data={
            "status": "processing",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processing"
