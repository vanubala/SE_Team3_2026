# Registration and assignment

Backend for UC1 Register Parcel and UC2 Assign Compartment (FR_02, FR_03, FR_04, NFR_04). The design is in `Software-Architecture/Modular-Design.md`, the sequence diagrams `SD-Register` and `SD-Assign`, and `Schemas-Endpoints.md`. The functions of each layer are listed in [CONTRACTS.md](CONTRACTS.md).

## Folders

| Folder | Contents |
|---|---|
| `app/controllers` | Routes, request and response bodies, error responses |
| `app/services` | Registration and assignment logic |
| `app/repositories` | Database access |
| `app/models.py` | Tables |

## Tests

Needs Python 3.12 or newer.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest --cov=app --cov-branch
```

The tests use an in-memory SQLite database. To run them on PostgreSQL as well, set `TEST_DATABASE_URL` to an empty database:

```
TEST_DATABASE_URL=postgresql+psycopg://user@localhost:5432/smart_locker_test .venv/bin/pytest
```

The tests in `tests/test_concurrency.py` only run on PostgreSQL. They send requests at the same time and check that a compartment is never reserved twice, that a parcel never gets two compartments, that a tracking number is never saved twice and that no compartment is reserved while its locker is being set offline (NFR_04).

## Run the API

Environment variables:

- `JWT_SECRET`: the secret used to sign tokens, at least 32 bytes.
- `PARCEL_ID_NAMESPACE`: a UUID, kept secret. Parcel IDs are made from the tracking number and this UUID.
- `DATABASE_URL`: for example `postgresql+psycopg://user:password@localhost/smart_locker`. With `sqlite:///local.sqlite3` the tables are created at startup. On PostgreSQL the tables must already exist (the migration in pull request #39 creates them).

```
.venv/bin/uvicorn --factory app.main:create_app --reload
```

API docs: `http://127.0.0.1:8000/docs`.

## Design decisions

- Reserving a compartment: the locker row is read with a shared lock and must be `ONLINE`. The compartment is then set to `RESERVED` with an update that only matches if it is still `AVAILABLE`. The compartment and the parcel are updated in the same transaction.
- IDs: all IDs are UUIDs. A request with an ID that is not a UUID gets 400. The courier ID is the token's `sub` claim.
- Only the courier who registered a parcel can assign it. Other couriers get 404.
- The pickup deadline is empty after registration. The deposit module sets it.
- `GET /api/lockers/{lockerId}/compartments` returns 409 when no available compartment fits.
- All errors use the error body of `Schemas-Endpoints.md` section 3. A 500 response does not show internal details.

## Other modules

- `app/models.py` is a copy of the tables in `Schemas-Endpoints.md`, so that this module can run on its own. The shared models are in Christos's `backend/` (pull request #39).
- Tokens come from the authentication module (pull request #39). This module accepts HS256 tokens with issuer `smart-locker-auth` and audience `smart-locker-api` (set with `JWT_ISSUER` and `JWT_AUDIENCE`) and the claims `sub` (the user's UUID), `role` (`COURIER`) and `exp`.
- `LockerRepository.reserve_compartment` has the same signature as in Raed's admin module (pull request #38).
