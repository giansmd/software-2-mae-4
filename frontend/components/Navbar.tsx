"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Waves, LogOut, User as UserIcon, Sun, Moon, Languages } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { clearToken, clearRole } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { useTheme } from "@/lib/theme";
import { Button } from "./ui/button";

const NAV_ITEMS = [
  { href: "/", label: "nav.dashboard" },
  { href: "/ml", label: "nav.ml" },
  { href: "/scenarios", label: "nav.scenarios", roles: ["INVESTIGADOR", "ADMIN"] },
  { href: "/measurements", label: "nav.measurements", roles: ["INVESTIGADOR", "ADMIN"] },
  { href: "/admin", label: "nav.admin", roles: ["ADMIN"] },
  { href: "/profile", label: "nav.profile", roles: ["INVESTIGADOR", "ADMIN"] },
];

export function Navbar() {
  const { user, isAuthed, role, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { t, lang, setLang } = useI18n();
  const { theme, toggleTheme } = useTheme();

  function handleLogout() {
    clearToken();
    clearRole();
    router.push("/login");
  }

  function canSee(roles?: string[]) {
    if (!roles) return true;
    return !!role && roles.includes(role);
  }

  return (
    <nav className="sticky top-0 z-40 w-full border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-gray-950/80">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Waves className="h-5 w-5 text-brand-500" />
          <span className="hidden sm:inline">{t("app.title")}</span>
        </Link>
        <div className="ml-4 hidden items-center gap-1 md:flex">
          {NAV_ITEMS.filter((i) => canSee(i.roles)).map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 ${
                pathname === item.href
                  ? "bg-gray-100 font-medium dark:bg-gray-800"
                  : "text-gray-600 dark:text-gray-300"
              }`}
            >
              {t(item.label)}
            </Link>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2">
          {/* Toggle idioma */}
          <div className="flex items-center overflow-hidden rounded-md border border-gray-300 dark:border-gray-700">
            <button
              type="button"
              onClick={() => setLang("es")}
              title={t("lang.toggle")}
              className={`px-2 py-1 text-xs font-semibold transition-colors ${
                lang === "es"
                  ? "bg-brand-500 text-white"
                  : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              }`}
            >
              ES
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              title={t("lang.toggle")}
              className={`px-2 py-1 text-xs font-semibold transition-colors ${
                lang === "en"
                  ? "bg-brand-500 text-white"
                  : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              }`}
            >
              EN
            </button>
          </div>
          {/* Toggle tema */}
          <button
            type="button"
            onClick={toggleTheme}
            title={t("theme.toggle")}
            className="flex h-8 w-8 items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>
          {loading ? (
            <span className="text-sm text-gray-400">…</span>
          ) : isAuthed && user ? (
            <>
              <span className="hidden text-sm text-gray-600 dark:text-gray-300 sm:inline">
                {user.full_name}{" "}
                <span className="rounded bg-brand-100 px-1.5 py-0.5 text-xs font-medium text-brand-800 dark:bg-brand-900 dark:text-brand-200">
                  {role}
                </span>
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/profile")}
                title={t("nav.profile.title")}
              >
                <UserIcon className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
                {t("nav.logout")}
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={() => router.push("/login")}>
              {t("nav.login")}
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
}