from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class EmbeddingVector(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, _dialect):
        if value is None:
            return value
        return [float(entry) for entry in value]

    def process_result_value(self, value, _dialect):
        if value is None:
            return value
        return [float(entry) for entry in value]


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_embeddings_document_chunk"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(EmbeddingVector(), nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    document: Mapped["Document"] = relationship(back_populates="embeddings")
