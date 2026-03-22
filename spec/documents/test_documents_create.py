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
    assert payload["status"] == "pending"
    assert payload["original_filename"] == "budget.txt"
    assert payload["has_embeddings"] is True


def test_create_document_accepts_explicit_status(client, auth_headers):
    response = client.post(
        "/documents",
        headers=auth_headers,
        data={
            "name": "Queued Budget",
            "description": "Waiting for enrichment",
            "document_type": "national_budget",
            "status": "processing",
        },
        files={
            "file": ("budget.txt", b"Budget allocation for health and education.", "text/plain"),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "processing"


def test_create_document_rejects_invalid_status(client, auth_headers):
    response = client.post(
        "/documents",
        headers=auth_headers,
        data={
            "name": "Bad Budget",
            "status": "archived",
        },
        files={
            "file": ("budget.txt", b"Budget allocation for health and education.", "text/plain"),
        },
    )

    assert response.status_code == 422
    assert response.json()["status"] == ["invalid value"]
