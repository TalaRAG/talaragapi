from psycopg import ProgrammingError
from pgvector.psycopg import register_vector
from sqlalchemy import create_engine, event
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
        if self.engine.dialect.name == "postgresql":
            @event.listens_for(self.engine, "connect")
            def _register_pgvector(dbapi_connection, _connection_record):
                try:
                    register_vector(dbapi_connection)
                except ProgrammingError:
                    # The extension may not exist yet on freshly created databases.
                    pass

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
