# Registration and assignment (UC1, UC2)

Parcel registration and compartment assignment for couriers: FR_02, FR_03, FR_04 and NFR_04. The design is in `docs/Software-Architecture/Modular-Design.md`, the sequence diagrams `SD-Register` and `SD-Assign`, and `Schemas-Endpoints.md` sections 2.2 and 2.3.

## Files

| Layer | Files |
|---|---|
| Controllers | `app/controllers/registration_controller.py`, `assignment_controller.py`, `parcel_dependencies.py`, `parcel_http_errors.py` |
| Schemas | `app/schemas/parcels.py` |
| Services | `app/services/registration_service.py`, `assignment_service.py`, `sizes.py`, `parcel_errors.py` |
| Repositories | `app/repositories/parcel_repository.py`, `locker_repository.py`, `unit_of_work.py` |
| Tests | `tests/register_assign/` |

## Routes

All routes need a courier token (`require_courier`): 401 without a valid token, 403 for another role.

| Route | Response | Errors |
|---|---|---|
| `POST /api/parcels` | 201, the registered parcel | 400, 401, 403, 409, 503 |
| `GET /api/parcels?status=REGISTERED` | 200, the courier's parcels | 400, 401, 403 |
| `GET /api/lockers/{lockerId}/compartments?size=MEDIUM` | 200, the available compartments and the recommended one | 400, 401, 403, 404, 409 |
| `POST /api/parcels/{parcelId}/assign` | 200, the assignment | 400, 401, 403, 404, 409 |

| Error | Status |
|---|---|
| `InvalidParcelData`, invalid body, ID that is not a UUID | 400 |
| `ParcelNotFound`, `LockerNotFound`, `CompartmentNotFound` | 404 |
| `DuplicateTrackingNumber`, `ParcelNotRegistered`, `LockerUnavailable`, `NoCompartmentAvailable`, `CompartmentTooSmall`, `CompartmentTaken` | 409 |
| Database error | 503 |

## RegistrationService

| | `register_parcel` | `list_parcels` |
|---|---|---|
| Input | courier ID, parcel form | courier ID, status (optional) |
| Returns | the saved parcel | the courier's parcels, oldest first |
| Errors | `InvalidParcelData`, `DuplicateTrackingNumber` | `InvalidParcelData` (unknown status) |
| Rules | one parcel per tracking number; recipient contact is an email address or a phone number with country code (`+352621123456`); status `REGISTERED`; pickup deadline empty; nothing saved on error | only the courier's own parcels |

## AssignmentService

| | `get_available_and_recommended_compartments` | `assign_compartment` |
|---|---|---|
| Input | locker ID, parcel size | courier ID, parcel ID, locker ID, compartment ID |
| Returns | the recommended compartment (the smallest that fits) and all fitting `AVAILABLE` compartments, smallest first | the parcel and the compartment |
| Errors | `InvalidParcelData`, `LockerNotFound`, `LockerUnavailable`, `NoCompartmentAvailable` | `ParcelNotFound` (also for another courier's parcel), `ParcelNotRegistered`, `LockerNotFound`, `LockerUnavailable`, `CompartmentNotFound`, `CompartmentTooSmall`, `CompartmentTaken` |
| Rules | only compartments of an `ONLINE` locker | only the courier who registered the parcel can assign it; a compartment is never reserved for two parcels at the same time and a parcel gets one compartment (NFR_04); nothing changed on error |

## ParcelRepository

| Function | Input | Returns |
|---|---|---|
| `exists_by_tracking_number` | tracking number | true or false |
| `save` | new parcel | nothing; raises `DuplicateTrackingNumber` or the database error |
| `find_by_id` | parcel ID | the parcel or `None` |
| `find_by_courier` | courier ID, status (optional) | the parcels, oldest first |
| `update_assignment` | parcel ID, compartment ID | true if the parcel was `REGISTERED` and is now `ASSIGNED` |

## LockerRepository

The four functions that assignment needs. `reserve_compartment` has the same signature as in the admin module (pull request #38).

| Function | Input | Returns |
|---|---|---|
| `find_locker` | locker ID | the locker or `None` |
| `find_compartment` | compartment ID | the compartment or `None` |
| `find_available_compartments` | locker ID, sizes | the `AVAILABLE` compartments of those sizes |
| `reserve_compartment` | locker ID, compartment ID | true if the locker is `ONLINE` and the compartment was `AVAILABLE` and is now `RESERVED` |

## Design decisions

- Reserving a compartment: the locker row is read with a shared lock and must be `ONLINE`. The compartment is then set to `RESERVED` with an update that only matches if it is still `AVAILABLE`. The compartment and the parcel are updated in the same transaction.
- Parcel IDs are uuid5 of the tracking number in the namespace `PARCEL_ID_NAMESPACE` (FR_03). Without that setting, a random namespace is used at each start; IDs already saved stay valid.
- Only the courier who registered a parcel can assign it. Other couriers get 404.
- The pickup deadline is empty after registration. The deposit module sets it.
- `GET /api/lockers/{lockerId}/compartments` returns 409 when no available compartment fits.

## Tests

`tests/register_assign/` runs on in-memory SQLite, and also on PostgreSQL when `TEST_DATABASE_URL` is set. `test_concurrency.py` only runs on PostgreSQL: it sends requests at the same time and checks that a compartment is never reserved twice, that a parcel never gets two compartments, that a tracking number is never saved twice and that no compartment is reserved while its locker is being set offline (NFR_04).
