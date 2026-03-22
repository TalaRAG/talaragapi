from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.helpers.api_helpers import password_match
from app.models.user import User
from app.operations.users.seed import DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, Seed


def build_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()
    return engine, session


def test_seed_creates_default_admin_user():
    engine, session = build_session()

    try:
        cmd = Seed(session)
        cmd.execute()

        user = session.scalar(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))

        assert cmd.created is True
        assert user is not None
        assert user.email == DEFAULT_ADMIN_EMAIL
        assert user.first_name == "Admin"
        assert user.last_name == "User"
        assert user.status == "active"
        assert user.is_admin is True
        assert password_match(DEFAULT_ADMIN_PASSWORD, user.password_hash)
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_seed_updates_existing_default_admin_user():
    engine, session = build_session()

    try:
        existing = User(
            email=DEFAULT_ADMIN_EMAIL,
            first_name="Legacy",
            last_name="Account",
            password_hash="stale-hash",
            status="inactive",
            is_admin=False,
        )
        session.add(existing)
        session.commit()

        cmd = Seed(session)
        cmd.execute()

        users = session.execute(select(User).where(User.email == DEFAULT_ADMIN_EMAIL)).scalars().all()
        user = users[0]

        assert cmd.created is False
        assert len(users) == 1
        assert user.first_name == "Admin"
        assert user.last_name == "User"
        assert user.status == "active"
        assert user.is_admin is True
        assert password_match(DEFAULT_ADMIN_PASSWORD, user.password_hash)
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
