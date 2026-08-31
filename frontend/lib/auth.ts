"use client";

import { useCallback, useEffect, useState } from "react";
import type { User } from "./types";
import { getMe } from "./api";

const TOKEN_KEY = "hd_token";
const ROLE_KEY = "hd_role";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function getRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ROLE_KEY);
}

export function setRole(role: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ROLE_KEY, role);
}

export function clearRole(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ROLE_KEY);
}

export function isAuthed(): boolean {
  return getToken() !== null;
}

/**
 * Hook de autenticación mínimo: carga el usuario actual desde /auth/me
 * si hay token y expone estado de autenticación, rol y funciones.
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await getMe();
      setUser(me);
      setRole(me.role);
    } catch {
      setUser(null);
      clearToken();
      clearRole();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const logout = useCallback(() => {
    clearToken();
    clearRole();
    setUser(null);
  }, []);

  return {
    user,
    loading,
    isAuthed: user !== null,
    role: user?.role ?? null,
    refresh,
    logout,
  };
}
