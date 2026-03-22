from sqlalchemy import func, select

from app.models.document_embedding import DocumentEmbedding
from spec.factories import DocumentEmbeddingFactory


def test_document_has_many_embeddings(db_session, document):
    embedding_a = DocumentEmbeddingFactory(document=document, chunk_index=0, embedding=[0.1, 0.2], dimensions=2)
    embedding_b = DocumentEmbeddingFactory(document=document, chunk_index=1, embedding=[0.3, 0.4], dimensions=2)

    db_session.refresh(document)

    assert [entry.id for entry in document.embeddings] == [embedding_a.id, embedding_b.id]
    assert document.embeddings[0].document_id == document.id


def test_deleting_document_removes_embeddings(db_session, document):
    DocumentEmbeddingFactory(document=document, chunk_index=0, embedding=[0.1, 0.2], dimensions=2)
    DocumentEmbeddingFactory(document=document, chunk_index=1, embedding=[0.3, 0.4], dimensions=2)

    db_session.delete(document)
    db_session.commit()

    count = db_session.scalar(select(func.count()).select_from(DocumentEmbedding))
    assert count == 0
