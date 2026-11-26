import { createContext, useContext, useState, type ReactNode } from "react";
import { authApi } from "../api/authApi";
import { sessionStorageHelper } from "../api/client";
import type { AuthUser } from "../types/domain";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = sessionStorageHelper.getUserRaw();
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  });

  const login = async (email: string, password: string): Promise<AuthUser> => {
    const res = await authApi.login(email, password);
    const fullUser: AuthUser = {
      ...res.user,
      email: res.user.email ?? email.trim().toLowerCase(),
    };
    sessionStorageHelper.setSession(res.token, JSON.stringify(fullUser));
    setUser(fullUser);
    return fullUser;
  };

  const logout = () => {
    sessionStorageHelper.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: user !== null, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
