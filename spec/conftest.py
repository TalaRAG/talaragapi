import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.db import Base, db
from app.helpers.api_helpers import build_jwt_header, generate_jwt
from spec.factories import UserFactory


@pytest.fixture()
def app():
    os.environ["APP_ENV"] = "test"
    application = create_app("spec.settings.TestConfig")
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
    yield session
    session.close()
    UserFactory._meta.sqlalchemy_session = None


@pytest.fixture()
def auth_headers(app, db_session):
    user = UserFactory(status="active")
    token = generate_jwt(user.to_dict(), app.state.settings.SECRET_KEY)
    return build_jwt_header(token)
