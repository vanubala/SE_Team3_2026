# Admin Locker Monitoring & Management (UC5)

`AdminLockerController`, `LockerManagementService` and `LockerRepository` for **FR_09** and **FR_10**, following `Modular-Design.md`, `Software-Architecture.md` and `Schemas-Endpoints.md`.

## Run

Needs Python 3.12+. From this folder:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python run_demo.py   # then open http://127.0.0.1:8000/docs
```

## Endpoints (role `ADMIN`)

| Endpoint | Purpose |
|---|---|
| `GET /api/admin/lockers` | All stations, occupancy and compartments |
| `PATCH /api/admin/compartments/{compartmentId}/status` | `{"status": "AVAILABLE"}` or `{"status": "MAINTENANCE"}` |
| `PATCH /api/admin/lockers/{lockerId}` | `{"operationalStatus": "ONLINE"}`, `OFFLINE` or `MAINTENANCE` |

Additions to the contract in `Schemas-Endpoints.md`, to be agreed by the team:

- `occupancy` also has `occupancyRate` (reserved + occupied, in % of total) and `availableBySize`, required by `Modular-Design.md`.
- PATCH responses have an extra `warning` text when an active parcel is affected.

FR_10's "Unavailable" is mapped to `OFFLINE` for stations.

## Rules

- A compartment cannot become `AVAILABLE` while linked to an `ASSIGNED`, `READY_FOR_PICKUP` or `EXPIRED` parcel (409).
- It can be put in `MAINTENANCE` with a parcel, with a warning.
- Changing a station leaves its compartments' own statuses untouched.
- Row locks and the `version` column prevent lost updates (NFR_04).

## Integration

```python
app.include_router(AdminLockerController(require_admin, get_session).router)
register_error_handlers(app)
```

- **Database/Auth:** replace `models.py` with the shared models and `auth.py` with the shared RBAC dependency. The role is `ADMIN`, as in the contract.
- **Assignment:** call `LockerRepository.reserve_compartment` and link the parcel in the same transaction. It refuses stations that are not `ONLINE`.
- **Deposit / Pickup:** use `occupy_compartment` / `release_compartment`. Both return `False` if the compartment is in `MAINTENANCE`. A pickup may still complete, but the compartment must stay in `MAINTENANCE`. The team still has to decide whether a deposit into a compartment blocked after assignment is allowed.
- Repository methods never commit; the calling service does.

## Limits

Tests use SQLite. They check that the generated PostgreSQL statements lock rows, but have not been run against a PostgreSQL server. Confirmation from locker hardware and "last known status" caching are not implemented.
