"""Guest collection and terminal security rules (UC4: FR_01, FR_08, NFR_02, NFR_03).

No HTTP or SQL here: the controller maps the exceptions below to responses,
and the repository does the queries. This service owns the transaction.
"""
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
from app.db.models import CompartmentStatus, ParcelStatus, PickupCode
from app.repositories.pickup_repository import PickupRepository
from app.security.pickup_codes import (InvalidPickupSession, PickupCodeHasher, PickupSession,
                                       PickupSessionTokens, generate_pickup_code)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)
# Failures further apart than this are not "consecutive" and start a new count.
FAILURE_WINDOW = timedelta(minutes=15)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    # SQLite returns naive datetimes; every timestamp we store is UTC.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class PickupError(Exception):
    pass


class LockerNotFound(PickupError):
    pass


class ParcelNotFound(PickupError):
    pass


class TerminalLocked(PickupError):
    def __init__(self, retry_after_seconds: int):
        super().__init__('Terminal locked after too many failed attempts')
        self.retry_after_seconds = retry_after_seconds


class InvalidPickupCode(PickupError):
    def __init__(self, remaining_attempts: int):
        super().__init__('Invalid or expired pickup code')
        self.remaining_attempts = remaining_attempts


class PickupSessionRejected(PickupError):
    pass


class CollectionConflict(PickupError):
    pass


@dataclass(frozen=True)
class UnlockResult:
    parcel_id: UUID
    compartment_id: UUID
    compartment_number: int
    session_token: str


@dataclass(frozen=True)
class CollectionResult:
    parcel_id: UUID
    status: str
    compartment_status: str


class PickupService:
    def __init__(self, repo: PickupRepository, hasher: PickupCodeHasher,
                 sessions: PickupSessionTokens, clock: Callable[[], datetime] = utcnow):
        self.repo = repo
        self.hasher = hasher
        self.sessions = sessions
        self.clock = clock

    def verify_and_unlock(self, locker_id: UUID, pickup_code: str) -> UnlockResult:
        now = self.clock()
        if self.repo.find_locker(locker_id) is None:
            raise LockerNotFound()
        try:
            state = self.repo.lock_terminal_state(locker_id)
            locked_until = _aware(state.locked_until)
            if locked_until is not None and locked_until > now:
                # Reject without checking the code, so a lockout cannot be used to keep guessing.
                self.repo.commit()
                raise TerminalLocked(math.ceil((locked_until - now).total_seconds()))
            if locked_until is not None:
                state.failed_attempts, state.locked_until, state.last_failed_at = 0, None, None
            last_failed = _aware(state.last_failed_at)
            if last_failed is not None and now - last_failed >= FAILURE_WINDOW:
                state.failed_attempts = 0

            match = self.repo.find_active_code(locker_id, self.hasher.hash(pickup_code), now)
            if match is None:
                state.failed_attempts += 1
                state.last_failed_at = now
                if state.failed_attempts >= MAX_FAILED_ATTEMPTS:
                    state.locked_until = now + LOCKOUT_DURATION
                    self.repo.commit()
                    raise TerminalLocked(int(LOCKOUT_DURATION.total_seconds()))
                remaining = MAX_FAILED_ATTEMPTS - state.failed_attempts
                self.repo.commit()
                raise InvalidPickupCode(remaining)

            _code, parcel, compartment = match
            state.failed_attempts, state.last_failed_at, state.locked_until = 0, None, None
            self.repo.commit()
        except PickupError:
            raise
        except Exception:
            self.repo.rollback()
            raise
        # The code stays valid until the door closes (confirm), so a recipient
        # whose door fails to open can retry instead of losing their parcel.
        token = self.sessions.issue(PickupSession(parcel.parcel_id, compartment.compartment_id, locker_id), now)
        return UnlockResult(parcel.parcel_id, compartment.compartment_id,
                            compartment.compartment_number, token)

    def confirm_collection(self, parcel_id: UUID, compartment_id: UUID, session_token: str,
                           door_closed: bool, parcel_detected: bool) -> CollectionResult:
        try:
            session = self.sessions.verify(session_token)
        except InvalidPickupSession as exc:
            raise PickupSessionRejected() from exc
        if session.parcel_id != parcel_id or session.compartment_id != compartment_id:
            raise PickupSessionRejected()
        if not door_closed:
            raise CollectionConflict('Compartment door is still open')
        if parcel_detected:
            raise CollectionConflict('Parcel is still detected in the compartment')

        now = self.clock()
        try:
            parcel = self.repo.lock_parcel(parcel_id)
            if parcel is None:
                raise ParcelNotFound()
            compartment = self.repo.lock_compartment(compartment_id)
            if compartment is None or parcel.compartment_id != compartment_id \
                    or compartment.locker_id != session.locker_id:
                raise CollectionConflict('Parcel is not stored in this compartment')
            if parcel.status == ParcelStatus.COLLECTED:
                # Retried confirm after a dropped connection: report the same outcome.
                self.repo.commit()
                return CollectionResult(parcel.parcel_id, parcel.status, compartment.status)
            code = self.repo.lock_code_for_parcel(parcel_id)
            if parcel.status != ParcelStatus.READY_FOR_PICKUP or code is None or code.used_at is not None:
                raise CollectionConflict('Parcel is not awaiting pickup')

            parcel.status = ParcelStatus.COLLECTED
            parcel.collected_at = now
            code.used_at = now  # single-use: invalidated on door closure (NFR_02)
            if compartment.status == CompartmentStatus.OCCUPIED:
                compartment.status = CompartmentStatus.AVAILABLE
                compartment.version += 1
            # A compartment an admin put into MAINTENANCE stays there.
            self.repo.commit()
            return CollectionResult(parcel.parcel_id, parcel.status, compartment.status)
        except Exception:
            self.repo.rollback()
            raise


class PickupCodeIssuer:
    """Creates a parcel's single-use PIN. Called by the deposit flow (UC3).

    Returns the plain PIN for the notification gateway; only its hash is kept.
    The caller's transaction commits it together with the deposit.
    """
    MAX_GENERATION_TRIES = 20

    def __init__(self, repo: PickupRepository, hasher: PickupCodeHasher,
                 clock: Callable[[], datetime] = utcnow):
        self.repo = repo
        self.hasher = hasher
        self.clock = clock

    def issue(self, parcel_id: UUID, locker_id: UUID, expires_at: datetime) -> str:
        now = self.clock()
        for _ in range(self.MAX_GENERATION_TRIES):
            code = generate_pickup_code()
            code_hash = self.hasher.hash(code)
            # A PIN must identify exactly one parcel at its station.
            if not self.repo.code_hash_in_use(locker_id, code_hash, now):
                break
        else:
            raise RuntimeError('Could not generate a unique pickup code')
        existing = self.repo.lock_code_for_parcel(parcel_id)
        if existing is None:
            self.repo.add(PickupCode(parcel_id=parcel_id, code_hash=code_hash, failed_attempts=0,
                                     issued_at=now, expires_at=expires_at))
        else:
            existing.code_hash, existing.issued_at, existing.expires_at = code_hash, now, expires_at
            existing.used_at, existing.failed_attempts, existing.locked_until = None, 0, None
        return code
