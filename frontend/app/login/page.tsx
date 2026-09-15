"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Waves, Loader2 } from "lucide-react";
import { login, register } from "@/lib/api";
import { setToken, setRole } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { useI18n } from "@/lib/i18n";

export default function LoginPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [institution, setInstitution] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      let res;
      if (mode === "login") {
        res = await login(email, password);
      } else {
        res = await register({
          email,
          password,
          full_name: fullName,
          institution: institution || undefined,
        });
      }
      setToken(res.access_token);
      setRole(res.user.role);
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(String((err as { message?: string })?.message ?? err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex items-center gap-2 text-brand-500">
            <Waves className="h-6 w-6" />
            <span className="text-lg font-semibold">Gemelo Digital</span>
          </div>
          <CardTitle>
            {mode === "login" ? t("login.title") : t("login.crearCuenta")}
          </CardTitle>
          <CardDescription>
            {mode === "login" ? t("login.accede") : t("login.registrateVisitante")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === "register" && (
              <input
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                placeholder={t("login.nombreCompleto")}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            )}
            <input
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              type="email"
              placeholder={t("login.email")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            {mode === "register" && (
              <input
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                placeholder={t("login.institucion")}
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
              />
            )}
            <input
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              type="password"
              placeholder={t("login.password")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && (
              <p className="text-sm text-error-600 dark:text-error-400">{error}</p>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {mode === "login" ? t("login.entrar") : t("login.registrarse")}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">
            {mode === "login" ? (
              <>
                {t("login.noTienesCuenta")}{" "}
                <button
                  className="text-brand-500 underline"
                  onClick={() => setMode("register")}
                >
                  {t("login.registrate")}
                </button>
              </>
            ) : (
              <>
                {t("login.yaTienesCuenta")}{" "}
                <button
                  className="text-brand-500 underline"
                  onClick={() => setMode("login")}
                >
                  {t("login.iniciaSesion")}
                </button>
              </>
            )}
          </p>
          <p className="mt-2 text-center text-xs">
            <Link href="/" className="text-gray-400 hover:underline">
              {t("login.volverDashboard")}
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
