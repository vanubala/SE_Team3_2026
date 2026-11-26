import {
  TerminalApiError,
  type DepositConfirmResponse,
  type DepositUnlockResponse,
  type PickupConfirmResponse,
  type PickupVerifyResponse,
} from "../types/terminal";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000/api";

async function postJson<T>(
  path: string,
  body: Record<string, unknown>
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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

  confirmDeposit: (parcelId: string, compartmentNumber: number) =>
    postJson<DepositConfirmResponse>("/terminal/deposit/confirm", {
      parcelId,
      compartmentNumber,
      doorClosed: true,
      parcelDetected: true,
    }),

  // UC4: Guest Recipient Pick-Up
  verifyPickupPin: (lockerId: string, pickupCode: string) =>
    postJson<PickupVerifyResponse>("/terminal/pickup/verify", {
      lockerId,
      pickupCode,
    }),

  confirmPickup: (parcelId: string, compartmentId: string) =>
    postJson<PickupConfirmResponse>("/terminal/pickup/confirm", {
      parcelId,
      compartmentId,
      doorClosed: true,
    }),
};
