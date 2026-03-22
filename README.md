# TalaragAPI

API for the Talarag Project.

## Quick Start

```bash
cp .env.example .env
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python -m app.cli doctor
python -m app.cli db.create
python -m app.cli db.upgrade
python -m app.cli db.seed
python -m app.cli server
```

Run specs with:

```bash
python -m app.cli spec
```

## Docker Compose

For Docker-based runs, use `.env.production` and pass it explicitly with `--env-file` so the app boots with `APP_ENV=production`.
Review and update `.env.production` before the first build, especially `SECRET_KEY` and the external database connection values.

Build the application image:

```bash
docker compose --env-file .env.production build
```

With this setup, Docker Compose only runs the API container. Your production database must already be reachable from the app container using the credentials in `.env.production`.
If the database is running on the Docker host, set `DB_HOST=host.docker.internal`. The bundled Compose file maps that hostname to Docker's host gateway so it also resolves on Linux.
If the database runs in another container on the same Compose project or Docker network, use that container or service name instead of `host.docker.internal`.

Create and migrate the production database from the app container:

```bash
docker compose --env-file .env.production run --rm app python -m app.cli db.create
docker compose --env-file .env.production run --rm app python -m app.cli db.upgrade
```

If you also want to load the default admin seed:

```bash
docker compose --env-file .env.production run --rm app python -m app.cli db.seed
```

Start the full stack:

```bash
docker compose --env-file .env.production up -d
```

Run future migration-related commands through Docker with the same env file:

```bash
docker compose --env-file .env.production run --rm app python -m app.cli db.upgrade
docker compose --env-file .env.production run --rm app python -m app.cli db.downgrade --revision -1
docker compose --env-file .env.production run --rm app python -m app.cli db.current
docker compose --env-file .env.production run --rm app python -m app.cli db.history
```

## High-Level Setup

## 1. Install dependencies
Create a virtual environment and install the project requirements:

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## 2. Configure environment variables
Create your local environment file from the template:

```bash
cp .env.example .env
```

By default, the project reads:
- `.env` when `APP_ENV=development`
- `.env.test` when `APP_ENV=test`

Important variables:
- `APP_ENV`: active environment, usually `development` or `test`
- `SECRET_KEY`: JWT signing key
- `CORS_ALLOW_ORIGINS`, `CORS_ALLOW_METHODS`, `CORS_ALLOW_HEADERS`, `CORS_ALLOW_CREDENTIALS`, `CORS_MAX_AGE`: browser cross-origin settings for the API
- `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL settings
- `DB_ADMIN_DATABASE`: existing PostgreSQL database used by `db.create` for the initial admin connection. Defaults to `postgres`.
- `DATABASE_URL`: optional full database URL override
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`: AWS credentials and region for S3 or SQS connections
- `STORAGE_*`: local or S3-backed file storage settings
  `STORAGE_MAX_CONTENT_LENGTH_MB` defaults to `500`
- `SQS_QUEUE`: queue name or URL for background message publishing

With the default values, the app expects PostgreSQL databases named:
- `default_api_fast_development`
- `default_api_fast_test`

When `STORAGE_SERVICE=s3`, configure `STORAGE_S3_BUCKET` and AWS credentials via `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`. `AWS_REGION` is the default region used for AWS clients; `STORAGE_S3_REGION` remains available as an optional S3-specific override.

Validate your environment, AWS connectivity, and database access with:

```bash
python -m app.cli doctor
```

## 3. Create and migrate the database
Create the configured development database:

```bash
python -m app.cli db.create
python -m app.cli db.upgrade
python -m app.cli db.seed
```

Create the test database:

```bash
APP_ENV=test python -m app.cli db.create
APP_ENV=test python -m app.cli db.upgrade
APP_ENV=test python -m app.cli db.seed
```

The seed command creates or refreshes the default admin account:

```text
email: admin@example.com
password: password
```

For document embeddings, PostgreSQL must have the `pgvector` extension available. The document embeddings migration enables it with `CREATE EXTENSION IF NOT EXISTS vector`, so your Postgres server needs the extension installed.

## 4. Run specs
Run the full spec suite:

```bash
python -m app.cli spec
```

Run a single spec file:

```bash
python -m app.cli spec spec/users/test_create.py
```

Filter by keyword:

```bash
python -m app.cli spec --keyword create
```

Optional convenience wrapper:

```bash
./bin/spec
./bin/spec spec/users/test_create.py
```

## 5. Start the development server
Run the local FastAPI server with reload enabled:

```bash
python -m app.cli server
```

This starts Uvicorn on `http://127.0.0.1:3000`.

Useful development endpoints:
- `GET /health`
- `POST /login`
- `GET /users`
- `POST /uploads`
