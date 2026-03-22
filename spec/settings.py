import os
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")

from config import Config, _load_database_config  # noqa: E402


_db_config = _load_database_config()


class TestConfig(Config):
    APP_ENV = "test"
    SQLALCHEMY_DATABASE_URI = _db_config.get(
        "uri",
        "postgresql+psycopg://postgres:postgres@localhost:5432/talaragapi_test",
    )
    SECRET_KEY = "test-secret-32-bytes-minimum-key"
    CORS_ALLOW_ORIGINS = ["http://localhost:8000"]
    CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_MAX_AGE = 600
    STORAGE_SERVICE = os.getenv("STORAGE_SERVICE", "local")
    STORAGE_LOCAL_ROOT = os.getenv("STORAGE_LOCAL_ROOT", str(Path("storage_test")))
    STORAGE_LOCAL_PUBLIC_ENDPOINT = os.getenv("STORAGE_LOCAL_PUBLIC_ENDPOINT", "/files")
