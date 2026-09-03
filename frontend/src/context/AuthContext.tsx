import { createContext, ReactNode, useContext, useMemo, useState } from "react";
import { api } from "../lib/api";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  national_id?: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function loadUser(): User | null {
  const value = localStorage.getItem("globalpay_user");
  if (!value) return null;
  try {
    return JSON.parse(value) as User;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(loadUser);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("globalpay_token")
  );

  async function login(email: string, password: string): Promise<User> {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const { data } = await api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });
    localStorage.setItem("globalpay_token", data.access_token);
    localStorage.setItem("globalpay_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function register(payload: RegisterPayload): Promise<void> {
    await api.post("/auth/register", payload);
  }

  function logout() {
    localStorage.removeItem("globalpay_token");
    localStorage.removeItem("globalpay_user");
    setUser(null);
    setToken(null);
  }

  const value = useMemo(
    () => ({ user, token, login, register, logout }),
    [user, token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
