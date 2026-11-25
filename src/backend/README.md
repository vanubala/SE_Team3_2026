# Smart Parcel Locker MVP backend

Shared PostgreSQL models, migrations, demo data, and staff authentication for the Smart Parcel Locker System.

## Start locally

Use Python 3.12+ and Docker Compose. From the repository root in PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe init_dev_env.py
docker compose up -d --wait
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.db.seed --demo
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

On Linux or macOS, use `python3` (3.12 or later) to create the environment and `.venv/bin/python` for the remaining Python commands. If you already have PostgreSQL 16, create a development database, set its `DATABASE_URL` in `.env`, and skip Compose.

`init_dev_env.py` generates credentials in the ignored `.env` file and preserves an existing file. Seed only a development database. The seed can be rerun and preserves existing passwords and states. Use `docker compose down` to stop the database and keep its data.

Open [Swagger](http://127.0.0.1:8000/docs) and try `POST /api/auth/login` with these demo accounts and the corresponding passwords in `.env`:

| Email | Role | Password variable |
| --- | --- | --- |
| `courier@example.test` | `COURIER` | `DEMO_COURIER_PASSWORD` |
| `admin@example.test` | `ADMIN` | `DEMO_ADMIN_PASSWORD` |

## Use the shared backend

Login accepts JSON with `email` and `password`. A successful response contains:

```json
{"token":"<signed JWT>","user":{"userId":"<UUID>","name":"Demo Courier","role":"COURIER"}}
```

Send `Authorization: Bearer <token>` to protected routes. The role guards return the verified user's UUID and role. Use that UUID for courier-owned queries. Missing or invalid authentication returns 401, and an authenticated user with the wrong role gets 403. Malformed input returns 400. Errors use `timestamp`, `status`, `error` and `message`.

Import `get_db` from `app.db.session`, `require_admin`, `require_courier` or `current_user` from `app.security.dependencies`, and shared models from `app.db.models`. Use the same session for operations that must succeed together. Run Alembic to create or update shared tables. See [integration notes](docs/CONTRACTS.md) for details.

## Run tests

The full suite needs a disposable PostgreSQL database for its three native tests. They create and clean up their own schemas. For the fresh Compose development database above, run these commands from `backend/`:

```powershell
$env:TEST_DATABASE_URL = ((Get-Content .env | Where-Object { $_ -like 'DATABASE_URL=*' }) -replace '^DATABASE_URL=','')
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov-branch --cov-report=term-missing
Remove-Item Env:TEST_DATABASE_URL
```

On Linux or macOS, export `TEST_DATABASE_URL` with the URL for your disposable database before running Pytest. Without that variable, the three native tests are skipped.

Final local check: **58 passed, 0 skipped** on PostgreSQL 16.16. Both staff roles logged in through Uvicorn. A temporary check also confirmed Raed's locker overview works with the shared models and role guard.
