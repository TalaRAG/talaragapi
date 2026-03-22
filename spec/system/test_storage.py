import pytest

from app.storage import init_storage
from config import Config


def test_default_storage_service_is_s3():
    assert Config.STORAGE_SERVICE == "s3"


def test_s3_storage_requires_bucket():
    class Settings:
        STORAGE_SERVICE = "s3"
        STORAGE_S3_BUCKET = ""
        STORAGE_S3_REGION = ""
        STORAGE_S3_ENDPOINT = ""

    with pytest.raises(ValueError, match="STORAGE_S3_BUCKET"):
        init_storage(Settings())
