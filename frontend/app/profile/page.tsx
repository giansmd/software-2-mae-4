"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import {
  getMe,
  updateMe,
  changePassword,
  ApiError,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ProfilePage() {
  const router = useRouter();
  const { t } = useI18n();
  const { isAuthed, refresh, loading: authLoading } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [institution, setInstitution] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthed) {
      router.push("/login");
      return;
    }
    getMe()
      .then((u) => {
        setFullName(u.full_name);
        setEmail(u.email);
        setInstitution(u.institution ?? "");
      })
      .catch((e) => {
        const ae = e as ApiError;
        if (ae?.status === 401) router.push("/login");
        else setError(String(ae?.message ?? e));
      })
      .finally(() => setLoading(false));
  }, [authLoading, isAuthed, router]);

  async function handleProfile(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      await updateMe({
        full_name: fullName,
        email,
        institution: institution || undefined,
      });
      await refresh();
      setSuccess(t("profile.actualizado"));
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    }
  }

  async function handlePassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(t("profile.passwordActualizada"));
      setCurrentPassword("");
      setNewPassword("");
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
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">{t("profile.title")}</h1>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-md border border-emerald-300 bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
          {success}
        </div>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{t("profile.datos")}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfile} className="space-y-3">
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              placeholder={t("profile.nombreCompleto")}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              type="email"
              placeholder={t("profile.correo")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              placeholder={t("profile.institucion")}
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
            />
            <Button type="submit">{t("profile.guardarPerfil")}</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("profile.cambiarPassword")}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePassword} className="space-y-3">
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              type="password"
              placeholder={t("profile.passwordActual")}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              type="password"
              placeholder={t("profile.passwordNueva")}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <Button type="submit">{t("profile.cambiarPasswordBtn")}</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
