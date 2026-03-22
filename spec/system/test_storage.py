import pytest

import app.storage as storage
from app.storage import init_storage
from config import Config


def test_default_storage_service_is_s3():
    assert Config.STORAGE_SERVICE == "s3"


def test_s3_storage_requires_bucket():
    class Settings:
        STORAGE_SERVICE = "s3"
        STORAGE_S3_BUCKET = ""
        STORAGE_S3_REGION = ""
        AWS_REGION = ""
        STORAGE_S3_ENDPOINT = ""

    with pytest.raises(ValueError, match="STORAGE_S3_BUCKET"):
        init_storage(Settings())


def test_s3_storage_uses_aws_region_when_storage_region_is_unset(monkeypatch):
    calls = []

    class Settings:
        STORAGE_SERVICE = "s3"
        STORAGE_S3_BUCKET = "documents"
        STORAGE_S3_REGION = ""
        AWS_REGION = "ap-southeast-1"
        STORAGE_S3_ENDPOINT = ""

    def fake_client(service_name, region_name=None, endpoint_url=None):
        calls.append(
            {
                "service_name": service_name,
                "region_name": region_name,
                "endpoint_url": endpoint_url,
            }
        )
        return object()

    monkeypatch.setattr(storage, "_storage_s3_client", None)
    monkeypatch.setattr(storage.boto3, "client", fake_client)

    init_storage(Settings())

    assert calls == [
        {
            "service_name": "s3",
            "region_name": "ap-southeast-1",
            "endpoint_url": None,
        }
    ]
