def test_rerun_document_enqueues_pending_document(client, admin_auth_headers, document, db_session, monkeypatch):
    enqueued = []
    document.status = "pending"
    db_session.add(document)
    db_session.commit()

    def fake_enqueue_document(settings, document_id, key):
        enqueued.append({"document_id": document_id, "key": key})
        return True

    monkeypatch.setattr("app.controllers.documents_controller.configured_sqs_queue", lambda: "documents.fifo")
    monkeypatch.setattr("app.controllers.documents_controller.enqueue_document", fake_enqueue_document)

    response = client.post(f"/documents/{document.id}/rerun", headers=admin_auth_headers)

    assert response.status_code == 200
    assert enqueued == [{"document_id": document.id, "key": document.storage_key}]


def test_rerun_document_rejects_non_pending_document(client, admin_auth_headers, document):
    response = client.post(f"/documents/{document.id}/rerun", headers=admin_auth_headers)

    assert response.status_code == 422
    assert response.json() == {"message": "document must be pending"}
