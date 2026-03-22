def test_public_documents_include_download_url(client, document):
    response = client.get("/public/documents")

    assert response.status_code == 200
    payload = response.json()
    assert payload["records"][0]["id"] == document.id
    assert payload["records"][0]["status"] == document.status
    assert payload["records"][0]["download_url"].endswith(document.storage_key)


def test_public_document_types_returns_configured_types(client):
    response = client.get("/public/document_types")

    assert response.status_code == 200
    assert "national_budget" in response.json()["document_types"]
