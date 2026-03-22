# TalaragAPI

API for the Talarag Project.

## Quick Start

```bash
cp .env.example .env
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python -m app.cli db.create
python -m app.cli db.upgrade
python -m app.cli server
```

Run specs with:

```bash
python -m app.cli spec
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
- `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL settings
- `DATABASE_URL`: optional full database URL override
- `STORAGE_*`: local or S3-backed file storage settings

With the default values, the app expects PostgreSQL databases named:
- `default_api_fast_development`
- `default_api_fast_test`

## 3. Create and migrate the database
Create the configured development database:

```bash
python -m app.cli db.create
python -m app.cli db.upgrade
```

Create the test database:

```bash
APP_ENV=test python -m app.cli db.create
APP_ENV=test python -m app.cli db.upgrade
```

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
