def test_create_document(client, auth_headers):
    response = client.post(
        "/documents",
        headers=auth_headers,
        data={
            "name": "2026 National Budget",
            "description": "Executive summary",
            "document_type": "national_budget",
        },
        files={
            "file": ("budget.txt", b"Budget allocation for health and education.", "text/plain"),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "2026 National Budget"
    assert payload["document_type"] == "national_budget"
    assert payload["original_filename"] == "budget.txt"
    assert payload["has_embeddings"] is True
