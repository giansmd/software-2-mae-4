"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Plus,
  Trash2,
  Pencil,
  FileText,
  FileSpreadsheet,
  FileDown,
  Loader2,
  Sliders,
} from "lucide-react";
import {
  getScenarios,
  createScenario,
  updateScenario,
  deleteScenario,
  downloadReport,
  ApiError,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Scenario, SeaLevelRise } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ScenariosPage() {
  const router = useRouter();
  const { isAuthed, role, loading: authLoading } = useAuth();
  const canExport = role === "INVESTIGADOR" || role === "ADMIN";
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Scenario | null>(null);
  const [busy, setBusy] = useState(false);

  // form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [restoration_level, setRestorationLevel] = useState(50);
  const [sea_level_rise, setSeaLevelRise] =
    useState<SeaLevelRise>("medium");
  const [horizon_year, setHorizonYear] = useState(2050);
  const [baseline_area_ha, setBaselineArea] = useState(100);
  const [baseline_carbon_density, setBaselineCarbon] = useState(50);
  const [is_public, setIsPublic] = useState(false);

  function requireAuth() {
    if (!isAuthed) {
      router.push("/login");
      return false;
    }
    return true;
  }

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getScenarios();
      setScenarios(data);
    } catch (e) {
      const ae = e as ApiError;
      if (ae?.status === 401 || ae?.status === 403) {
        router.push("/login");
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

  function openCreate() {
    if (!requireAuth()) return;
    setEditing(null);
    setName("");
    setDescription("");
    setRestorationLevel(50);
    setSeaLevelRise("medium");
    setHorizonYear(2050);
    setBaselineArea(100);
    setBaselineCarbon(50);
    setIsPublic(false);
    setShowForm(true);
  }

  function openEdit(s: Scenario) {
    if (!requireAuth()) return;
    setEditing(s);
    setName(s.name);
    setDescription(s.description ?? "");
    setRestorationLevel(s.restoration_level);
    setSeaLevelRise(s.sea_level_rise);
    setHorizonYear(s.horizon_year);
    setBaselineArea(s.baseline_area_ha);
    setBaselineCarbon(s.baseline_carbon_density);
    setIsPublic(s.is_public);
    setShowForm(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!requireAuth()) return;
    setBusy(true);
    setError(null);
    const payload = {
      name,
      description: description || undefined,
      restoration_level,
      sea_level_rise,
      horizon_year,
      baseline_area_ha: baseline_area_ha,
      baseline_carbon_density: baseline_carbon_density,
      is_public,
    };
    try {
      if (editing) {
        await updateScenario(editing.id, payload);
      } else {
        await createScenario(payload);
      }
      setShowForm(false);
      await load();
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id: number) {
    if (!requireAuth()) return;
    if (!confirm("¿Eliminar este escenario?")) return;
    setBusy(true);
    try {
      await deleteScenario(id);
      await load();
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport(id: number, fmt: "pdf" | "docx" | "xlsx") {
    if (!requireAuth()) return;
    try {
      await downloadReport(id, fmt);
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
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Escenarios</h1>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" /> Nuevo escenario
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      {showForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>
              {editing ? "Editar escenario" : "Crear escenario"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Nombre"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                placeholder="Descripción (opcional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <label className="text-sm">
                Nivel de restauración (%): {restoration_level}
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={restoration_level}
                  onChange={(e) => setRestorationLevel(Number(e.target.value))}
                  className="w-full"
                />
              </label>
              <label className="text-sm">
                Aumento nivel del mar
                <select
                  value={sea_level_rise}
                  onChange={(e) =>
                    setSeaLevelRise(e.target.value as SeaLevelRise)
                  }
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                >
                  <option value="low">Bajo</option>
                  <option value="medium">Medio</option>
                  <option value="high">Alto</option>
                </select>
              </label>
              <label className="text-sm">
                Año horizonte
                <input
                  type="number"
                  value={horizon_year}
                  onChange={(e) => setHorizonYear(Number(e.target.value))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                />
              </label>
              <label className="text-sm">
                Superficie base (ha)
                <input
                  type="number"
                  value={baseline_area_ha}
                  onChange={(e) => setBaselineArea(Number(e.target.value))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                />
              </label>
              <label className="text-sm">
                Densidad carbono base (t/ha)
                <input
                  type="number"
                  value={baseline_carbon_density}
                  onChange={(e) =>
                    setBaselineCarbon(Number(e.target.value))
                  }
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                />
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={is_public}
                  onChange={(e) => setIsPublic(e.target.checked)}
                />
                Escenario público
              </label>
              <div className="flex gap-2 md:col-span-2">
                <Button type="submit" disabled={busy}>
                  {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                  Guardar
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForm(false)}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {scenarios.length === 0 ? (
        <p className="text-slate-500">No hay escenarios todavía.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {scenarios.map((s) => (
            <Card key={s.id}>
              <CardHeader>
                <CardTitle className="flex items-start justify-between gap-2">
                  <span>{s.name}</span>
                  {s.is_public && (
                    <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                      Público
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-2 text-sm text-slate-500">
                  {s.description || "Sin descripción"}
                </p>
                <dl className="mb-3 grid grid-cols-2 gap-y-1 text-xs text-slate-600 dark:text-slate-300">
                  <dt>Restauración:</dt>
                  <dd>{s.restoration_level}%</dd>
                  <dt>Nivel mar:</dt>
                  <dd>{s.sea_level_rise}</dd>
                  <dt>Horizonte:</dt>
                  <dd>{s.horizon_year}</dd>
                  <dt>Superficie:</dt>
                  <dd>{s.baseline_area_ha} ha</dd>
                </dl>
                <div className="flex flex-wrap gap-2">
                  <Link href={`/scenarios/${s.id}`}>
                    <Button size="sm" variant="secondary">
                      <Sliders className="h-4 w-4" /> Simular
                    </Button>
                  </Link>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => openEdit(s)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-red-600"
                    onClick={() => handleDelete(s.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                {canExport && (
                  <div className="mt-3 flex gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleExport(s.id, "pdf")}
                    >
                      <FileText className="h-4 w-4" /> PDF
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleExport(s.id, "docx")}
                    >
                      <FileDown className="h-4 w-4" /> Word
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleExport(s.id, "xlsx")}
                    >
                      <FileSpreadsheet className="h-4 w-4" /> Excel
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </main>
  );
}
