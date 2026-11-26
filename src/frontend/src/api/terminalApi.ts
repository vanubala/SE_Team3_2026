import {
  TerminalApiError,
  type DepositConfirmResponse,
  type DepositUnlockResponse,
  type PickupConfirmResponse,
  type PickupVerifyResponse,
} from "../types/terminal";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000/api";
// Credential of this physical terminal, bound to its locker station
// (backend: python -m app.security.terminal_auth <locker_id>).
const TERMINAL_TOKEN = import.meta.env.VITE_TERMINAL_TOKEN as string | undefined;

async function postJson<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(TERMINAL_TOKEN ? { Authorization: `Bearer ${TERMINAL_TOKEN}` } : {}),
      },
      body: JSON.stringify(body),
    });
  } catch {
    throw new TerminalApiError("Unable to reach locker server.", "NETWORK");
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.message || "Terminal operation failed.";
    if (res.status === 401) {
      throw new TerminalApiError(msg, "INVALID_CODE", {
        remainingAttempts: data.remainingAttempts,
      });
    }
    if (res.status === 423 || res.status === 429) {
      throw new TerminalApiError(msg, "LOCKED", {
        retryAfterSeconds: data.retryAfterSeconds ?? 900,
      });
    }
    if (res.status === 404) {
      throw new TerminalApiError(msg, "NOT_FOUND");
    }
    if (res.status === 409) {
      throw new TerminalApiError(msg, "CONFLICT");
    }
    throw new TerminalApiError(msg, "NETWORK");
  }

  return data as T;
}

export const terminalApi = {
  // UC3: Courier Drop-Off
  unlockForDeposit: (lockerId: string, parcelId: string) =>
    postJson<DepositUnlockResponse>("/terminal/deposit/unlock", {
      lockerId,
      parcelId,
    }),

  confirmDeposit: (parcelId: string, compartmentId: string) =>
    postJson<DepositConfirmResponse>("/terminal/deposit/confirm", {
      parcelId,
      compartmentId,
      doorClosed: true,
      parcelDetected: true,
    }),

  // UC4: Guest Recipient Pick-Up
  verifyPickupPin: (lockerId: string, pickupCode: string) =>
    postJson<PickupVerifyResponse>("/terminal/pickup/verify", {
      lockerId,
      pickupCode,
    }),

  confirmPickup: (
    parcelId: string,
    compartmentId: string,
    pickupSessionToken: string
  ) =>
    postJson<PickupConfirmResponse>("/terminal/pickup/confirm", {
      parcelId,
      compartmentId,
      doorClosed: true,
      pickupSessionToken,
    }),
};
