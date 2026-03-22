import shutil
import uuid
from pathlib import Path
from urllib.parse import quote

import boto3
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from werkzeug.utils import secure_filename


_storage_s3_client = None


def init_storage(settings):
    service = settings.STORAGE_SERVICE
    if service == "local":
        root = Path(settings.STORAGE_LOCAL_ROOT).resolve()
        root.mkdir(parents=True, exist_ok=True)
    elif service == "s3":
        _get_s3_client(settings)
    else:
        raise ValueError(f"Unsupported STORAGE_SERVICE: {service}")


def store_file(upload: UploadFile, settings, filename=None):
    service = settings.STORAGE_SERVICE
    if service == "local":
        return _store_local(upload, settings, filename)
    if service == "s3":
        return _store_s3(upload, settings, filename)
    raise ValueError(f"Unsupported STORAGE_SERVICE: {service}")


def local_file_response(key, settings):
    if settings.STORAGE_SERVICE != "local":
        raise HTTPException(status_code=404, detail="not found")

    root = Path(settings.STORAGE_LOCAL_ROOT).resolve()
    target_path = (root / key).resolve()
    if root not in target_path.parents and target_path != root:
        raise HTTPException(status_code=404, detail="not found")
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(target_path)


def _store_local(upload, settings, filename=None):
    root = Path(settings.STORAGE_LOCAL_ROOT).resolve()
    safe_name = _build_filename(upload.filename, filename)
    key = _build_key(safe_name)
    target_path = root / key
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("wb") as handle:
        upload.file.seek(0)
        shutil.copyfileobj(upload.file, handle)

    public_endpoint = settings.STORAGE_LOCAL_PUBLIC_ENDPOINT.rstrip("/")
    public_url = f"{public_endpoint}/{quote(key)}"
    return _file_result(key, safe_name, upload.content_type, target_path.stat().st_size, public_url)


def _store_s3(upload, settings, filename=None):
    bucket = settings.STORAGE_S3_BUCKET
    if not bucket:
        raise ValueError("STORAGE_S3_BUCKET must be set when STORAGE_SERVICE=s3")

    safe_name = _build_filename(upload.filename, filename)
    key = _build_key(safe_name, settings.STORAGE_S3_PREFIX)
    client = _get_s3_client(settings)

    extra_args = {}
    if upload.content_type:
        extra_args["ContentType"] = upload.content_type
    if settings.STORAGE_S3_ACL:
        extra_args["ACL"] = settings.STORAGE_S3_ACL

    upload.file.seek(0)
    if extra_args:
        client.upload_fileobj(upload.file, bucket, key, ExtraArgs=extra_args)
    else:
        client.upload_fileobj(upload.file, bucket, key)
    public_url = _build_s3_public_url(bucket, key, settings, client)
    return _file_result(key, safe_name, upload.content_type, None, public_url)


def _build_filename(original, override):
    name = override or original or "file"
    return secure_filename(name) or "file"


def _build_key(filename, prefix=""):
    prefix = (prefix or "").strip("/")
    unique = uuid.uuid4().hex
    key = f"{unique}-{filename}"
    return f"{prefix}/{key}" if prefix else key


def _build_s3_public_url(bucket, key, settings, client):
    if settings.STORAGE_S3_PUBLIC_URL:
        base = settings.STORAGE_S3_PUBLIC_URL.rstrip("/")
        return f"{base}/{quote(key)}"

    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=int(settings.STORAGE_S3_PRESIGNED_EXPIRES_IN),
    )


def _get_s3_client(settings):
    global _storage_s3_client
    if _storage_s3_client is not None:
        return _storage_s3_client

    region = settings.STORAGE_S3_REGION or None
    endpoint = settings.STORAGE_S3_ENDPOINT or None
    _storage_s3_client = boto3.client("s3", region_name=region, endpoint_url=endpoint)
    return _storage_s3_client


def _file_result(key, filename, content_type, size, url):
    return {
        "key": key,
        "filename": filename,
        "content_type": content_type,
        "byte_size": size,
        "url": url,
    }
