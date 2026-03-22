import app.storage as storage


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


def test_create_document_still_succeeds_when_storage_closes_upload_stream(client, app, auth_headers, monkeypatch):
    def fake_store_file(upload, _settings, filename=None):
        content = upload.file.read()
        upload.file.close()
        return {
            "key": "documents/closed-stream.txt",
            "filename": filename or upload.filename,
            "content_type": upload.content_type,
            "byte_size": len(content),
            "url": "https://downloads.example/documents/closed-stream.txt",
        }

    monkeypatch.setattr("app.operations.documents.save.store_file", fake_store_file)

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
    assert payload["storage_key"] == "documents/closed-stream.txt"
    assert payload["has_embeddings"] is True


def test_create_document_enqueues_pending_document(client, auth_headers, monkeypatch):
    enqueued = []

    def fake_enqueue_document(settings, document_id, key):
        enqueued.append({"document_id": document_id, "key": key})
        return True

    monkeypatch.setattr("app.controllers.documents_controller.configured_sqs_queue", lambda: "documents.fifo")
    monkeypatch.setattr("app.controllers.documents_controller.enqueue_document", fake_enqueue_document)

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
    assert enqueued == [{"document_id": payload["id"], "key": payload["storage_key"]}]


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


def test_create_document_uploads_file_to_s3(client, app, auth_headers, monkeypatch):
    uploads = []

    class FakeS3Client:
        def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):
            uploads.append(
                {
                    "bucket": bucket,
                    "key": key,
                    "content": fileobj.read(),
                    "extra_args": ExtraArgs or {},
                }
            )

        def generate_presigned_url(self, _operation, Params=None, ExpiresIn=None):
            return f"https://downloads.example/{Params['Key']}?expires={ExpiresIn}"

    fake_client = FakeS3Client()

    monkeypatch.setattr(app.state.settings, "STORAGE_SERVICE", "s3", raising=False)
    monkeypatch.setattr(app.state.settings, "STORAGE_S3_BUCKET", "documents", raising=False)
    monkeypatch.setattr(app.state.settings, "STORAGE_S3_PREFIX", "uploads", raising=False)
    monkeypatch.setattr(app.state.settings, "STORAGE_S3_ACL", "", raising=False)
    monkeypatch.setattr(app.state.settings, "STORAGE_S3_PUBLIC_URL", "", raising=False)
    monkeypatch.setattr(app.state.settings, "STORAGE_S3_PRESIGNED_EXPIRES_IN", 3600, raising=False)
    monkeypatch.setattr(storage, "_storage_s3_client", None)
    monkeypatch.setattr(storage, "_get_s3_client", lambda _settings: fake_client)

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
    assert payload["storage_provider"] == "s3"
    assert payload["storage_key"].startswith("uploads/")
    assert payload["storage_key"].endswith("-budget.txt")
    assert len(uploads) == 1
    assert uploads[0] == {
        "bucket": "documents",
        "key": payload["storage_key"],
        "content": b"Budget allocation for health and education.",
        "extra_args": {"ContentType": "text/plain"},
    }
