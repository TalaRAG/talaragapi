import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path


def system_greet():
    print("hello world")


def _quote_identifier(name):
    return f"\"{name.replace('\"', '\"\"')}\""


def _ensure_sqlite_db(database_path):
    from sqlalchemy import create_engine

    if not database_path or database_path == ":memory:":
        print("SQLite in-memory database does not need creation.")
        return

    path = Path(database_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    engine.connect().close()
    print(f"SQLite database ready at {path}")


def create_database(settings):
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    database_uri = settings.SQLALCHEMY_DATABASE_URI
    if not database_uri:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI is not configured.")

    url = make_url(database_uri)
    if url.get_backend_name() == "sqlite":
        _ensure_sqlite_db(url.database)
        return

    db_name = url.database
    if not db_name:
        raise RuntimeError("Database name is missing from SQLALCHEMY_DATABASE_URI.")

    try:
        admin_url = url.set(database="postgres")
    except AttributeError:
        admin_url = url._replace(database="postgres")

    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        ).scalar()
        if exists:
            print(f"Database already exists: {db_name}")
            return

        connection.execute(text(f"CREATE DATABASE {_quote_identifier(db_name)}"))
        print(f"Database created: {db_name}")


def _active_settings():
    from app.environment import load_environment

    load_environment()
    from config import Config

    return Config


def _run_command(command, env=None):
    def _normalize_return_code(return_code):
        if return_code == -signal.SIGINT:
            return 130
        return return_code

    process = subprocess.Popen(
        command,
        env=env,
        start_new_session=True,
    )
    try:
        return _normalize_return_code(process.wait())
    except KeyboardInterrupt:
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            pass

        try:
            return _normalize_return_code(process.wait(timeout=5))
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            return _normalize_return_code(process.wait())


def _command_env():
    env = os.environ.copy()
    env["APP_ENV"] = os.getenv("APP_ENV", "development")
    return env


def run_server(args):
    command = ["uvicorn", "main:app", "--host", args.host, "--port", str(args.port)]
    if args.reload:
        command.append("--reload")
    return _run_command(command)


def run_spec(args):
    command = ["pytest", "spec"]
    if args.target:
        command.append(args.target)
    if args.keyword:
        command.extend(["-k", args.keyword])

    env = os.environ.copy()
    env["APP_ENV"] = "test"
    return _run_command(command, env=env)


def run_greet(_args):
    system_greet()
    return 0


def run_db_create(_args):
    create_database(_active_settings())
    return 0


def run_db_migrate(args):
    return _run_command(
        ["alembic", "revision", "--autogenerate", "-m", args.message],
        env=_command_env(),
    )


def run_db_upgrade(args):
    return _run_command(["alembic", "upgrade", args.revision], env=_command_env())


def run_db_downgrade(args):
    return _run_command(["alembic", "downgrade", args.revision], env=_command_env())


def run_db_history(_args):
    return _run_command(["alembic", "history"], env=_command_env())


def run_db_current(_args):
    return _run_command(["alembic", "current"], env=_command_env())


def run_routes(_args):
    settings = _active_settings()
    print(f"Mounted API prefix: {settings.API_PREFIX}")
    print("Routes: /health, /login, /users, /uploads, /files/{key}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Project command runner.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    server_parser = subparsers.add_parser("server", help="Run the development server")
    server_parser.add_argument("--host", default="127.0.0.1")
    server_parser.add_argument("--port", type=int, default=3000)
    server_parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable auto-reload",
    )
    server_parser.set_defaults(handler=run_server)

    spec_parser = subparsers.add_parser("spec", help="Run the test suite")
    spec_parser.add_argument("target", nargs="?", default="")
    spec_parser.add_argument("--keyword", default="")
    spec_parser.set_defaults(handler=run_spec)

    greet_parser = subparsers.add_parser("system.greet", help="Run the sample system task")
    greet_parser.set_defaults(handler=run_greet)

    db_create_parser = subparsers.add_parser("db.create", help="Create the configured database")
    db_create_parser.set_defaults(handler=run_db_create)

    db_migrate_parser = subparsers.add_parser("db.migrate", help="Generate a new migration")
    db_migrate_parser.add_argument("--message", default="update schema")
    db_migrate_parser.set_defaults(handler=run_db_migrate)

    db_upgrade_parser = subparsers.add_parser("db.upgrade", help="Apply migrations")
    db_upgrade_parser.add_argument("--revision", default="head")
    db_upgrade_parser.set_defaults(handler=run_db_upgrade)

    db_downgrade_parser = subparsers.add_parser("db.downgrade", help="Roll back migrations")
    db_downgrade_parser.add_argument("--revision", default="-1")
    db_downgrade_parser.set_defaults(handler=run_db_downgrade)

    db_history_parser = subparsers.add_parser("db.history", help="Show migration history")
    db_history_parser.set_defaults(handler=run_db_history)

    db_current_parser = subparsers.add_parser("db.current", help="Show current revision")
    db_current_parser.set_defaults(handler=run_db_current)

    routes_parser = subparsers.add_parser("routes", help="Print mounted routes")
    routes_parser.set_defaults(handler=run_routes)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
