import { ApiError } from "../types/domain";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000/api";
const TOKEN_KEY = "spls_token";
const USER_KEY = "spls_user";

export const sessionStorageHelper = {
  getToken: (): string | null => localStorage.getItem(TOKEN_KEY),
  setSession: (token: string, userJson: string): void => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, userJson);
  },
  getUserRaw: (): string | null => localStorage.getItem(USER_KEY),
  clear: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = sessionStorageHelper.getToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("Unable to reach the SPLS server.", 0, "NETWORK");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data.message || "Request failed.";
    if (response.status === 401) {
      sessionStorageHelper.clear();
      throw new ApiError(message, 401, "UNAUTHORIZED");
    }
    if (response.status === 403) {
      throw new ApiError("Insufficient role permissions.", 403, "FORBIDDEN");
    }
    if (response.status === 404) {
      throw new ApiError(message, 404, "NOT_FOUND");
    }
    if (response.status === 409) {
      throw new ApiError(message, 409, "CONFLICT");
    }
    if (response.status === 400 || response.status === 422) {
      throw new ApiError(message, response.status, "VALIDATION");
    }
    throw new ApiError(message, response.status, "NETWORK");
  }

  return data as T;
}
