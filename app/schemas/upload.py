from pydantic import BaseModel


class FileResult(BaseModel):
    key: str
    filename: str
    content_type: str | None = None
    byte_size: int | None = None
    url: str


class UploadResponse(BaseModel):
    file: FileResult
