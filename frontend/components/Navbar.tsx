"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Waves, LogOut, User as UserIcon } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { clearToken, clearRole } from "@/lib/auth";
import { Button } from "./ui/button";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/scenarios", label: "Escenarios", roles: ["INVESTIGADOR", "ADMIN"] },
  { href: "/measurements", label: "Mediciones", roles: ["INVESTIGADOR", "ADMIN"] },
  { href: "/admin", label: "Admin", roles: ["ADMIN"] },
  { href: "/profile", label: "Perfil", roles: ["INVESTIGADOR", "ADMIN"] },
];

export function Navbar() {
  const { user, isAuthed, role, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

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
    <nav className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Waves className="h-5 w-5 text-emerald-600" />
          <span>Gemelo Digital de Humedales</span>
        </Link>
        <div className="ml-4 hidden items-center gap-1 md:flex">
          {NAV_ITEMS.filter((i) => canSee(i.roles)).map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 ${
                pathname === item.href
                  ? "bg-slate-100 font-medium dark:bg-slate-800"
                  : "text-slate-600 dark:text-slate-300"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-3">
          {loading ? (
            <span className="text-sm text-slate-400">…</span>
          ) : isAuthed && user ? (
            <>
              <span className="hidden text-sm text-slate-600 dark:text-slate-300 sm:inline">
                {user.full_name}{" "}
                <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                  {role}
                </span>
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/profile")}
                title="Perfil"
              >
                <UserIcon className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
                Salir
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={() => router.push("/login")}>
              Ingresar
            </Button>
          )}
        </div>
      </div>
    </nav>
  );
}
