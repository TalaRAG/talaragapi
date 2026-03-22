import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import create_app
from app.db import Base, db
from app.helpers.api_helpers import build_jwt_header, generate_jwt
from spec.factories import DocumentEmbeddingFactory, DocumentFactory, UserFactory


@pytest.fixture()
def app():
    os.environ["APP_ENV"] = "test"
    application = create_app("spec.settings.TestConfig")
    if db.engine.dialect.name == "postgresql":
        with db.engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=db.engine)
    yield application
    Base.metadata.drop_all(bind=db.engine)
    storage_root = Path(application.state.settings.STORAGE_LOCAL_ROOT)
    if storage_root.exists():
        shutil.rmtree(storage_root)


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def db_session(app):
    session = db.session()
    UserFactory._meta.sqlalchemy_session = session
    DocumentFactory._meta.sqlalchemy_session = session
    DocumentEmbeddingFactory._meta.sqlalchemy_session = session
    yield session
    session.close()
    UserFactory._meta.sqlalchemy_session = None
    DocumentFactory._meta.sqlalchemy_session = None
    DocumentEmbeddingFactory._meta.sqlalchemy_session = None


@pytest.fixture()
def auth_headers(app, db_session):
    user = UserFactory(status="active")
    token = generate_jwt(user.to_dict(), app.state.settings.SECRET_KEY)
    return build_jwt_header(token)


@pytest.fixture()
def admin_auth_headers(app, db_session):
    user = UserFactory(status="active", is_admin=True)
    token = generate_jwt(user.to_dict(), app.state.settings.SECRET_KEY)
    return build_jwt_header(token)


@pytest.fixture()
def document(app, db_session):
    return DocumentFactory(
        name="Budget Primer",
        description="Budget allocation for health and education.",
        document_type="national_budget",
        original_filename="budget.txt",
        content_type="text/plain",
        size_bytes=43,
        storage_provider=app.state.settings.STORAGE_SERVICE,
        storage_key="documents/sample-budget.txt",
        status="done",
        extracted_text="Budget allocation for health and education.",
        has_embeddings=True,
    )
