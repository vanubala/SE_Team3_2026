import type { LoginResponse } from "../types/domain";
import { apiRequest } from "./client";

export const authApi = {
  login: (email: string, password: string): Promise<LoginResponse> =>
    apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    }),
};
