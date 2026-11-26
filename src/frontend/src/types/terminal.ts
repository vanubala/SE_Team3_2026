export type TerminalMode = 'PICKUP' | 'DEPOSIT';

export interface DepositUnlockResponse {
  parcelId: string;
  compartmentNumber: number;
  doorCommand: 'UNLOCK';
}

export interface DepositConfirmResponse {
  parcelId: string;
  status: 'READY_FOR_PICKUP';
  pickupDeadline: string;
  notificationTriggered: boolean;
}

export interface PickupVerifyResponse {
  parcelId: string;
  compartmentId: string;
  compartmentNumber: number;
  doorCommand: 'UNLOCK';
  /** Short-lived proof of a successful PIN check; required to confirm collection. */
  pickupSessionToken: string;
}

export interface PickupConfirmResponse {
  parcelId: string;
  status: 'COLLECTED';
  compartmentStatus: 'AVAILABLE' | 'MAINTENANCE';
}

export class TerminalApiError extends Error {
  readonly code: 'INVALID_CODE' | 'LOCKED' | 'NOT_FOUND' | 'CONFLICT' | 'NETWORK';
  readonly remainingAttempts?: number;
  readonly retryAfterSeconds?: number;

  constructor(
    message: string,
    code: TerminalApiError['code'],
    meta?: { remainingAttempts?: number; retryAfterSeconds?: number }
  ) {
    super(message);
    this.name = 'TerminalApiError';
    this.code = code;
    this.remainingAttempts = meta?.remainingAttempts;
    this.retryAfterSeconds = meta?.retryAfterSeconds;
  }
}