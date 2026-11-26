# Contracts: registration and assignment

## RegistrationService

| | `register_parcel` | `list_parcels` |
|---|---|---|
| Input | courier ID, parcel form | courier ID, status (optional) |
| Returns | the saved parcel | the courier's parcels, oldest first |
| Errors | `InvalidParcelData`, `DuplicateTrackingNumber`, `StorageError` | `InvalidParcelData` (unknown status) |
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
| `save` | new parcel | nothing; raises `DuplicateTrackingNumber` or `StorageError` |
| `find_by_id` | parcel ID | the parcel or `None` |
| `find_by_courier` | courier ID, status (optional) | the parcels, oldest first |
| `update_assignment` | parcel ID, compartment ID | true if the parcel was `REGISTERED` and is now `ASSIGNED` |

## LockerRepository

This module's `LockerRepository` has only the four functions that assignment needs. `reserve_compartment` has the same signature as in Raed's admin module (pull request #38).

| Function | Input | Returns |
|---|---|---|
| `find_locker` | locker ID | the locker or `None` |
| `find_compartment` | compartment ID | the compartment or `None` |
| `find_available_compartments` | locker ID, sizes | the `AVAILABLE` compartments of those sizes |
| `reserve_compartment` | locker ID, compartment ID | true if the locker is `ONLINE` and the compartment was `AVAILABLE` and is now `RESERVED` |

## Routes

| Route | Response | Errors |
|---|---|---|
| `POST /api/parcels` | 201, the registered parcel | 400, 401, 403, 409, 500 |
| `GET /api/parcels?status=REGISTERED` | 200, the courier's parcels | 400, 401, 403 |
| `GET /api/lockers/{lockerId}/compartments?size=MEDIUM` | 200, the available compartments and the recommended one | 400, 401, 403, 404, 409 |
| `POST /api/parcels/{parcelId}/assign` | 200, the assignment | 400, 401, 403, 404, 409 |

| Error | Status |
|---|---|
| `InvalidParcelData`, invalid body, ID that is not a UUID | 400 |
| `NotAuthenticated` (missing or invalid token) | 401 |
| `NotCourier` | 403 |
| `ParcelNotFound`, `LockerNotFound`, `CompartmentNotFound` | 404 |
| `DuplicateTrackingNumber`, `ParcelNotRegistered`, `LockerUnavailable`, `NoCompartmentAvailable`, `CompartmentTooSmall`, `CompartmentTaken` | 409 |
| `StorageError`, any other error | 500 |

All errors, including 404 for an unknown route and 405 for a wrong method, use the error body of `Schemas-Endpoints.md` section 3.
