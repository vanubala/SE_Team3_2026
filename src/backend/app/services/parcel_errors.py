"""Errors of parcel registration and assignment. controllers/parcel_http_errors.py maps them to HTTP status codes."""


class ParcelError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidParcelData(ParcelError):
    pass


class ParcelNotFound(ParcelError):
    pass


class LockerNotFound(ParcelError):
    pass


class CompartmentNotFound(ParcelError):
    pass


class DuplicateTrackingNumber(ParcelError):
    pass


class ParcelNotRegistered(ParcelError):
    pass


class LockerUnavailable(ParcelError):
    pass


class NoCompartmentAvailable(ParcelError):
    pass


class CompartmentTooSmall(ParcelError):
    pass


class CompartmentTaken(ParcelError):
    pass
