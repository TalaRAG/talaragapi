"""add document embeddings

Revision ID: 9f6a1c8b7e21
Revises: eb540d57900a
Create Date: 2026-03-22 14:30:00
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "9f6a1c8b7e21"
down_revision = "eb540d57900a"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_embeddings_document_chunk"),
    )
    op.create_index(op.f("ix_document_embeddings_document_id"), "document_embeddings", ["document_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_document_embeddings_document_id"), table_name="document_embeddings")
    op.drop_table("document_embeddings")
