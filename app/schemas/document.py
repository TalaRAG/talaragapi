from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    document_type: str | None = None
    original_filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    storage_provider: str
    storage_key: str
    status: str
    has_embeddings: bool
    download_url: str | None = None


class DocumentCollection(BaseModel):
    records: list[DocumentOut]
    total_pages: int
    current_page: int
    next_page: int | None
    prev_page: int | None
