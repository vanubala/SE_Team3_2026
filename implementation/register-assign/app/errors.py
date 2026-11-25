"""Errors of this module. controllers/http_errors.py maps them to HTTP status codes."""


class ModuleError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidParcelData(ModuleError):
    pass


class NotAuthenticated(ModuleError):
    pass


class NotCourier(ModuleError):
    pass


class ParcelNotFound(ModuleError):
    pass


class LockerNotFound(ModuleError):
    pass


class CompartmentNotFound(ModuleError):
    pass


class DuplicateTrackingNumber(ModuleError):
    pass


class ParcelNotRegistered(ModuleError):
    pass


class LockerUnavailable(ModuleError):
    pass


class NoCompartmentAvailable(ModuleError):
    pass


class CompartmentTooSmall(ModuleError):
    pass


class CompartmentTaken(ModuleError):
    pass


class StorageError(ModuleError):
    pass
