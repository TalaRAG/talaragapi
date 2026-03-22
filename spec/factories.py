import factory

from app.models.document import Document
from app.models.document_embedding import DocumentEmbedding
from app.helpers.api_helpers import build_password_hash
from app.models.user import User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    password_hash = factory.LazyFunction(lambda: build_password_hash("password"))
    status = "active"
    is_admin = False


class DocumentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Document
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Document {n}")
    description = factory.Faker("sentence")
    document_type = "national_budget"
    original_filename = factory.Sequence(lambda n: f"document-{n}.txt")
    content_type = "text/plain"
    size_bytes = 128
    storage_provider = "local"
    storage_key = factory.Sequence(lambda n: f"documents/document-{n}.txt")
    status = "pending"
    extracted_text = factory.Faker("paragraph")
    has_embeddings = True


class DocumentEmbeddingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = DocumentEmbedding
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    document = factory.SubFactory(DocumentFactory)
    chunk_index = factory.Sequence(lambda n: n)
    content = factory.Faker("paragraph")
    embedding = factory.LazyFunction(lambda: [0.1, 0.2, 0.3])
    embedding_model = "text-embedding-3-small"
    dimensions = factory.LazyAttribute(lambda entry: len(entry.embedding))
