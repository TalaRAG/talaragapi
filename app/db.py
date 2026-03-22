from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    def configure(self, database_url):
        if self.engine is not None:
            self.engine.dispose()

        self.engine = create_engine(database_url, future=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def session(self):
        if self.session_factory is None:
            raise RuntimeError("Database has not been configured.")
        return self.session_factory()


db = DatabaseManager()


def get_db():
    session = db.session()
    try:
        yield session
    finally:
        session.close()
