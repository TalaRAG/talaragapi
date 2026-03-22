import os
import re
from pathlib import Path

import yaml


_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
DEFAULT_DOCUMENT_TYPES = [
    "national_budget",
    "agency_budget",
    "project_program",
    "procurement_notice",
    "audit_report",
    "development_plan",
    "local_budget",
    "legislation_budget_related",
    "circular_guideline",
    "performance_report",
]
EXPORTED_ENV_VARS = [
    "APP_NAME",
    "APP_ENV",
    "API_PREFIX",
    "CORS_ALLOW_ORIGINS",
    "CORS_ALLOW_METHODS",
    "CORS_ALLOW_HEADERS",
    "CORS_ALLOW_CREDENTIALS",
    "CORS_MAX_AGE",
    "SECRET_KEY",
    "DATABASE_URL",
    "DB_ADMIN_DATABASE",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
    "STORAGE_SERVICE",
    "STORAGE_LOCAL_ROOT",
    "STORAGE_LOCAL_PUBLIC_ENDPOINT",
    "STORAGE_S3_BUCKET",
    "STORAGE_S3_REGION",
    "STORAGE_S3_ENDPOINT",
    "STORAGE_S3_PREFIX",
    "STORAGE_S3_PUBLIC_URL",
    "STORAGE_S3_PRESIGNED_EXPIRES_IN",
    "STORAGE_S3_ACL",
    "STORAGE_MAX_CONTENT_LENGTH_MB",
    "DOCUMENT_TYPES",
    "ADMIN_EMAILS",
    "INFERENCE_PROVIDER",
    "INFERENCE_SYSTEM_PROMPT",
    "INFERENCE_TOP_K_DEFAULT",
    "INFERENCE_STREAM_CHUNK_SIZE",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "OPENAI_TIMEOUT_SECONDS",
    "LLAMA_CPP_MODEL_PATH",
    "LLAMA_CPP_CHAT_FORMAT",
    "LLAMA_CPP_N_CTX",
    "LLAMA_CPP_N_THREADS",
    "LLAMA_CPP_N_GPU_LAYERS",
    "LLAMA_CPP_TEMPERATURE",
    "LLAMA_CPP_MAX_TOKENS",
]
PUBLIC_EXPORTED_ENV_VARS = [
    "APP_NAME",
    "APP_ENV",
    "API_PREFIX",
    "CORS_ALLOW_ORIGINS",
    "CORS_ALLOW_METHODS",
    "CORS_ALLOW_HEADERS",
    "CORS_ALLOW_CREDENTIALS",
    "CORS_MAX_AGE",
    "AWS_REGION",
    "STORAGE_SERVICE",
    "STORAGE_LOCAL_ROOT",
    "STORAGE_LOCAL_PUBLIC_ENDPOINT",
    "STORAGE_S3_BUCKET",
    "STORAGE_S3_REGION",
    "STORAGE_S3_ENDPOINT",
    "STORAGE_S3_PREFIX",
    "STORAGE_S3_PUBLIC_URL",
    "STORAGE_S3_PRESIGNED_EXPIRES_IN",
    "STORAGE_S3_ACL",
    "STORAGE_MAX_CONTENT_LENGTH_MB",
    "DOCUMENT_TYPES",
    "ADMIN_EMAILS",
    "INFERENCE_PROVIDER",
    "INFERENCE_SYSTEM_PROMPT",
    "INFERENCE_TOP_K_DEFAULT",
    "INFERENCE_STREAM_CHUNK_SIZE",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "OPENAI_TIMEOUT_SECONDS",
    "LLAMA_CPP_MODEL_PATH",
    "LLAMA_CPP_CHAT_FORMAT",
    "LLAMA_CPP_N_CTX",
    "LLAMA_CPP_N_THREADS",
    "LLAMA_CPP_N_GPU_LAYERS",
    "LLAMA_CPP_TEMPERATURE",
    "LLAMA_CPP_MAX_TOKENS",
]
SECRET_STATUS_ENV_VARS = [
    "OPENAI_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
]


def _expand_env_vars(value):
    if not isinstance(value, str):
        return value

    def _replace(match):
        return os.getenv(match.group(1), "")

    return _ENV_PATTERN.sub(_replace, value)


def _parse_csv(value, default=None):
    raw = value if value is not None else default
    if raw is None:
        return []
    return [entry.strip() for entry in str(raw).split(",") if entry.strip()]


def _parse_bool(value, default=False):
    raw = value if value is not None else default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _stringify_env_value(value):
    if isinstance(value, list):
        return ",".join(value)
    return str(value)


def _load_database_config():
    config_path = Path(os.getenv("DATABASE_YAML", "database.yaml"))
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    env = os.getenv("APP_ENV", "development")
    config = data.get(env, {})
    return {key: _expand_env_vars(value) for key, value in config.items()}


class Config:
    APP_NAME = os.getenv("APP_NAME", "talaragapi")
    APP_ENV = os.getenv("APP_ENV", "development")
    API_PREFIX = os.getenv("API_PREFIX", "")
    CORS_ALLOW_ORIGINS = _parse_csv(os.getenv("CORS_ALLOW_ORIGINS"), "*")
    CORS_ALLOW_METHODS = _parse_csv(os.getenv("CORS_ALLOW_METHODS"), "*")
    CORS_ALLOW_HEADERS = _parse_csv(os.getenv("CORS_ALLOW_HEADERS"), "*")
    CORS_ALLOW_CREDENTIALS = _parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), True)
    CORS_MAX_AGE = int(os.getenv("CORS_MAX_AGE", "600"))

    _db_config = _load_database_config()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        _db_config.get(
            "uri",
            "postgresql+psycopg://postgres:postgres@localhost:5432/talaragapi_development",
        ),
    )
    DB_ADMIN_DATABASE = os.getenv("DB_ADMIN_DATABASE", "postgres")
    SECRET_KEY = os.getenv("SECRET_KEY", "default-api-fast-secret")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "")

    STORAGE_SERVICE = os.getenv("STORAGE_SERVICE", "s3")
    STORAGE_LOCAL_ROOT = os.getenv("STORAGE_LOCAL_ROOT", str(Path("storage")))
    STORAGE_LOCAL_PUBLIC_ENDPOINT = os.getenv("STORAGE_LOCAL_PUBLIC_ENDPOINT", "/files")
    STORAGE_S3_BUCKET = os.getenv("STORAGE_S3_BUCKET", "")
    STORAGE_S3_REGION = os.getenv("STORAGE_S3_REGION", os.getenv("AWS_REGION", ""))
    STORAGE_S3_ENDPOINT = os.getenv("STORAGE_S3_ENDPOINT", "")
    STORAGE_S3_PREFIX = os.getenv("STORAGE_S3_PREFIX", "")
    STORAGE_S3_PUBLIC_URL = os.getenv("STORAGE_S3_PUBLIC_URL", "")
    STORAGE_S3_PRESIGNED_EXPIRES_IN = int(os.getenv("STORAGE_S3_PRESIGNED_EXPIRES_IN", "3600"))
    STORAGE_S3_ACL = os.getenv("STORAGE_S3_ACL", "")
    STORAGE_MAX_CONTENT_LENGTH_MB = int(os.getenv("STORAGE_MAX_CONTENT_LENGTH_MB", "100"))

    DOCUMENT_TYPES = _parse_csv(os.getenv("DOCUMENT_TYPES"), ",".join(DEFAULT_DOCUMENT_TYPES))
    ADMIN_EMAILS = _parse_csv(os.getenv("ADMIN_EMAILS"), "")

    INFERENCE_PROVIDER = os.getenv("INFERENCE_PROVIDER", "openai").lower()
    INFERENCE_SYSTEM_PROMPT = os.getenv(
        "INFERENCE_SYSTEM_PROMPT",
        (
            "You are TalaRAG, a document-grounded assistant. "
            "Answer only from the supplied context and say when the context is insufficient."
        ),
    )
    INFERENCE_TOP_K_DEFAULT = int(os.getenv("INFERENCE_TOP_K_DEFAULT", "5"))
    INFERENCE_STREAM_CHUNK_SIZE = int(os.getenv("INFERENCE_STREAM_CHUNK_SIZE", "96"))

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

    LLAMA_CPP_MODEL_PATH = os.getenv("LLAMA_CPP_MODEL_PATH", "")
    LLAMA_CPP_CHAT_FORMAT = os.getenv("LLAMA_CPP_CHAT_FORMAT", "")
    LLAMA_CPP_N_CTX = int(os.getenv("LLAMA_CPP_N_CTX", "4096"))
    LLAMA_CPP_N_THREADS = int(os.getenv("LLAMA_CPP_N_THREADS", "4"))
    LLAMA_CPP_N_GPU_LAYERS = int(os.getenv("LLAMA_CPP_N_GPU_LAYERS", "0"))
    LLAMA_CPP_TEMPERATURE = float(os.getenv("LLAMA_CPP_TEMPERATURE", "0.2"))
    LLAMA_CPP_MAX_TOKENS = int(os.getenv("LLAMA_CPP_MAX_TOKENS", "1024"))

    @classmethod
    def exported_environment(cls):
        values = {}
        for key in EXPORTED_ENV_VARS:
            if key == "DATABASE_URL":
                current = cls.SQLALCHEMY_DATABASE_URI
            else:
                current = getattr(cls, key, os.getenv(key, ""))
            values[key] = _stringify_env_value(current)
        return values

    @classmethod
    def public_environment(cls):
        values = {}
        for key in PUBLIC_EXPORTED_ENV_VARS:
            current = getattr(cls, key, os.getenv(key, ""))
            values[key] = _stringify_env_value(current)
        return values

    @classmethod
    def secret_statuses(cls):
        statuses = {}
        for key in SECRET_STATUS_ENV_VARS:
            current = getattr(cls, key, os.getenv(key, ""))
            statuses[key] = bool(str(current or "").strip())
        return statuses
