"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Loader2 } from "lucide-react";
import {
  getUsers,
  createUser,
  deleteUser,
  getModelParams,
  updateModelParam,
  ApiError,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { User, ModelParam, Role } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function AdminPage() {
  const { t } = useI18n();
  const router = useRouter();
  const { isAuthed, role, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [params, setParams] = useState<ModelParam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [institution, setInstitution] = useState("");
  const [userRole, setUserRole] = useState<Role>("INVESTIGADOR");

  function requireAdmin() {
    if (!isAuthed) {
      router.push("/login");
      return false;
    }
    if (role !== "ADMIN") {
      router.push("/");
      return false;
    }
    return true;
  }

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [u, p] = await Promise.all([getUsers(), getModelParams()]);
      setUsers(u);
      setParams(p);
    } catch (e) {
      const ae = e as ApiError;
      if (ae?.status === 401 || ae?.status === 403) {
        router.push(ae.status === 403 ? "/" : "/login");
        return;
      }
      setError(String(ae?.message ?? e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading]);

  async function handleCreateUser(e: React.FormEvent) {
    e.preventDefault();
    if (!requireAdmin()) return;
    setBusy(true);
    setError(null);
    try {
      await createUser({
        email,
        password,
        full_name: fullName,
        institution: institution || undefined,
        role: userRole,
      });
      setEmail("");
      setPassword("");
      setFullName("");
      setInstitution("");
      await load();
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteUser(id: number) {
    if (!requireAdmin()) return;
    if (!confirm("¿Eliminar usuario?")) return;
    setBusy(true);
    try {
      await deleteUser(id);
      await load();
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function handleParamChange(key: string, value: number) {
    if (!requireAdmin()) return;
    try {
      const updated = await updateModelParam(key, value);
      setParams((prev) => prev.map((p) => (p.key === key ? updated : p)));
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    }
  }

  if (loading || authLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">Administración</h1>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("admin.usuarios")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleCreateUser} className="grid grid-cols-2 gap-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Nombre completo"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Correo"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Contraseña"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Institución"
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
              />
              <select
                value={userRole}
                onChange={(e) => setUserRole(e.target.value as Role)}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              >
                <option value="INVESTIGADOR">INVESTIGADOR</option>
                <option value="ADMIN">ADMIN</option>
                <option value="VISITANTE">VISITANTE</option>
              </select>
              <Button type="submit" disabled={busy} className="col-span-2">
                {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                <Plus className="h-4 w-4" /> Crear usuario
              </Button>
            </form>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-500">
                  <tr>
                    <th className="py-2">Nombre</th>
                    <th className="py-2">Rol</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-t border-slate-200 dark:border-slate-800">
                      <td className="py-2">
                        {u.full_name}
                        <span className="block text-xs text-slate-400">
                          {u.email}
                        </span>
                      </td>
                      <td className="py-2">{u.role}</td>
                      <td className="py-2 text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-600"
                          onClick={() => handleDeleteUser(u.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("admin.calibracion")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {params.length === 0 ? (
              <p className="text-sm text-slate-500">
                No hay parámetros disponibles.
              </p>
            ) : (
              params.map((p) => (
                <div key={p.key} className="space-y-1">
                  <label className="flex items-center justify-between text-sm">
                    <span className="font-medium">{p.key}</span>
                    <span className="text-slate-400">{p.unit ?? ""}</span>
                  </label>
                  {p.description && (
                    <p className="text-xs text-slate-500">{p.description}</p>
                  )}
                  <input
                    type="number"
                    step="any"
                    defaultValue={p.value}
                    key={`${p.key}-${p.value}`}
                    onBlur={(e) =>
                      handleParamChange(p.key, Number(e.target.value))
                    }
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                  />
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
