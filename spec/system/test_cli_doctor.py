from types import SimpleNamespace

from app import cli


def _settings(**overrides):
    values = {
        "APP_ENV": "test",
        "STORAGE_SERVICE": "local",
        "STORAGE_S3_BUCKET": "",
        "STORAGE_S3_REGION": "",
        "STORAGE_S3_ENDPOINT": "",
        "AWS_REGION": "",
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://postgres:postgres@localhost:5432/talaragapi_test",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_check_environment_accepts_database_url_for_local_storage(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/talaragapi_test")
    monkeypatch.delenv("SQS_QUEUE", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)

    result = cli._check_environment(_settings())

    assert result == {
        "name": "environment",
        "status": "pass",
        "message": "required environment variables are set",
    }


def test_check_environment_reports_missing_aws_and_database_variables(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.setenv("DB_USERNAME", "postgres")
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.setenv("SQS_QUEUE", "documents")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)

    result = cli._check_environment(_settings(STORAGE_SERVICE="s3"))

    assert result["name"] == "environment"
    assert result["status"] == "fail"
    assert "AWS_ACCESS_KEY_ID" in result["message"]
    assert "AWS_SECRET_ACCESS_KEY" in result["message"]
    assert "DB_NAME" in result["message"]
    assert "DB_PASSWORD" in result["message"]
    assert "DB_PORT" in result["message"]
    assert "AWS_REGION or STORAGE_S3_REGION" in result["message"]
    assert "STORAGE_S3_BUCKET" in result["message"]


def test_check_environment_accepts_storage_and_sqs_regions_without_aws_region(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/talaragapi_test")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.setenv("SQS_QUEUE", "https://sqs.ap-southeast-1.amazonaws.com/123456789012/documents")

    result = cli._check_environment(
        _settings(
            STORAGE_SERVICE="s3",
            STORAGE_S3_BUCKET="documents",
            STORAGE_S3_REGION="ap-southeast-1",
        )
    )

    assert result == {
        "name": "environment",
        "status": "pass",
        "message": "required environment variables are set",
    }


def test_check_sqs_uses_local_endpoint_when_queue_url_is_non_aws(monkeypatch):
    calls = []

    class FakeSqsClient:
        def get_queue_attributes(self, QueueUrl, AttributeNames):
            calls.append(
                {
                    "queue_url": QueueUrl,
                    "attribute_names": AttributeNames,
                }
            )
            return {"Attributes": {"QueueArn": "arn:aws:sqs:ap-southeast-1:000000000000:documents"}}

    def fake_client(service_name, region_name=None, endpoint_url=None):
        calls.append(
            {
                "service_name": service_name,
                "region_name": region_name,
                "endpoint_url": endpoint_url,
            }
        )
        assert service_name == "sqs"
        return FakeSqsClient()

    monkeypatch.setenv("SQS_QUEUE", "http://localhost:4566/000000000000/documents")
    monkeypatch.setattr("boto3.client", fake_client)

    result = cli._check_sqs(_settings(AWS_REGION="ap-southeast-1"))

    assert result == {
        "name": "sqs",
        "status": "pass",
        "message": "reachable queue: http://localhost:4566/000000000000/documents",
    }
    assert calls == [
        {
            "service_name": "sqs",
            "region_name": "ap-southeast-1",
            "endpoint_url": "http://localhost:4566",
        },
        {
            "queue_url": "http://localhost:4566/000000000000/documents",
            "attribute_names": ["QueueArn"],
        },
    ]


def test_run_doctor_returns_non_zero_when_a_check_fails(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_active_settings", lambda: _settings(APP_ENV="development"))
    monkeypatch.setattr(
        cli,
        "_check_environment",
        lambda settings: {"name": "environment", "status": "pass", "message": "ok"},
    )
    monkeypatch.setattr(
        cli,
        "_check_s3",
        lambda settings: {"name": "s3", "status": "skip", "message": "not configured"},
    )
    monkeypatch.setattr(
        cli,
        "_check_sqs",
        lambda settings: {"name": "sqs", "status": "fail", "message": "queue unreachable"},
    )
    monkeypatch.setattr(
        cli,
        "_check_database",
        lambda settings: {"name": "database", "status": "pass", "message": "ok"},
    )

    exit_code = cli.run_doctor(None)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Doctor checks (APP_ENV=development)" in captured.out
    assert "[FAIL] sqs: queue unreachable" in captured.out
    assert "Summary: 2 passed, 1 failed, 1 skipped" in captured.out
