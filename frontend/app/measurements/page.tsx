"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, Pencil, Loader2 } from "lucide-react";
import {
  getMeasurements,
  createMeasurement,
  updateMeasurement,
  deleteMeasurement,
  getScenarios,
  ApiError,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Measurement, Scenario } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { TableExportButtons } from "@/components/ui/tableExportButtons";

const EMPTY = {
  date: new Date().toISOString().slice(0, 10),
  vegetation_cover: 0,
  water_table: 0,
  soil_organic_carbon: 0,
  biomass: 0,
  note: "",
  scenario_id: undefined as number | undefined,
};

export default function MeasurementsPage() {
  const { t } = useI18n();
  const router = useRouter();
  const { isAuthed, loading: authLoading } = useAuth();
  const [items, setItems] = useState<Measurement[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Measurement | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ ...EMPTY });
  const tableRef = useRef<HTMLTableElement>(null);

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
      const [m, s] = await Promise.all([getMeasurements(), getScenarios()]);
      setItems(m);
      setScenarios(s);
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
    setForm({ ...EMPTY });
    setShowForm(true);
  }

  function openEdit(m: Measurement) {
    if (!requireAuth()) return;
    setEditing(m);
    setForm({
      date: m.date,
      vegetation_cover: m.vegetation_cover,
      water_table: m.water_table,
      soil_organic_carbon: m.soil_organic_carbon,
      biomass: m.biomass,
      note: m.note ?? "",
      scenario_id: m.scenario_id ?? undefined,
    });
    setShowForm(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!requireAuth()) return;
    setBusy(true);
    setError(null);
    const payload = {
      date: form.date,
      vegetation_cover: Number(form.vegetation_cover),
      water_table: Number(form.water_table),
      soil_organic_carbon: Number(form.soil_organic_carbon),
      biomass: Number(form.biomass),
      note: form.note || undefined,
      scenario_id: form.scenario_id,
    };
    try {
      if (editing) {
        await updateMeasurement(editing.id, payload);
      } else {
        await createMeasurement(payload);
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
    if (!confirm("¿Eliminar esta medición?")) return;
    setBusy(true);
    try {
      await deleteMeasurement(id);
      await load();
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  const scenarioName = (sid: number | null) =>
    scenarios.find((s) => s.id === sid)?.name ?? "—";

  if (loading || authLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Mediciones</h1>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" /> Nueva medición
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-error-300 bg-error-50 p-3 text-sm text-error-700 dark:bg-error-950 dark:text-error-300">
          {error}
        </div>
      )}

      {showForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>
              {editing ? t("measurements.editar") : t("measurements.nueva")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <label className="text-sm">
                Fecha
                <input
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                  required
                />
              </label>
              <label className="text-sm">
                Escenario
                <select
                  value={form.scenario_id ?? ""}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      scenario_id: e.target.value
                        ? Number(e.target.value)
                        : undefined,
                    })
                  }
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                >
                  <option value="">— (ninguno)</option>
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                Cobertura vegetal (%)
                <input
                  type="number"
                  step="0.01"
                  value={form.vegetation_cover}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      vegetation_cover: Number(e.target.value),
                    })
                  }
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                />
              </label>
              <label className="text-sm">
                Nivel de agua (m)
                <input
                  type="number"
                  step="0.01"
                  value={form.water_table}
                  onChange={(e) =>
                    setForm({ ...form, water_table: Number(e.target.value) })
                  }
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                />
              </label>
              <label className="text-sm">
                C orgánico suelo (t/ha)
                <input
                  type="number"
                  step="0.01"
                  value={form.soil_organic_carbon}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      soil_organic_carbon: Number(e.target.value),
                    })
                  }
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                />
              </label>
              <label className="text-sm">
                Biomasa (t/ha)
                <input
                  type="number"
                  step="0.01"
                  value={form.biomass}
                  onChange={(e) =>
                    setForm({ ...form, biomass: Number(e.target.value) })
                  }
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                />
              </label>
              <label className="text-sm md:col-span-3">
                Nota
                <input
                  value={form.note}
                  onChange={(e) => setForm({ ...form, note: e.target.value })}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                />
              </label>
              <div className="flex gap-2 md:col-span-3">
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

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle>Registro de mediciones de campo</CardTitle>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Datos observados de cobertura vegetal, nivel freático, carbono orgánico del suelo y biomasa.
              </p>
            </div>
            <TableExportButtons
              tableRef={tableRef}
              filename="mediciones_humedal"
              description="Mediciones observadas de carbono, cobertura y nivel freático por escenario."
              source="Registro de mediciones del Gemelo Digital"
            />
          </div>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table ref={tableRef} className="w-full text-sm">
            <thead className="bg-gray-100 text-left text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              <tr>
                <th className="px-4 py-2">Fecha</th>
                <th className="px-4 py-2">Escenario</th>
                <th className="px-4 py-2">Cob. veg.</th>
                <th className="px-4 py-2">Nivel agua</th>
                <th className="px-4 py-2">C org.</th>
                <th className="px-4 py-2">Biomasa</th>
                <th className="px-4 py-2">Nota</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-gray-500">
                    No hay mediciones.
                  </td>
                </tr>
              ) : (
                items.map((m) => (
                  <tr
                    key={m.id}
                    className="border-t border-gray-200 dark:border-gray-800"
                  >
                    <td className="px-4 py-2">{m.date}</td>
                    <td className="px-4 py-2">{scenarioName(m.scenario_id)}</td>
                    <td className="px-4 py-2">{m.vegetation_cover}</td>
                    <td className="px-4 py-2">{m.water_table}</td>
                    <td className="px-4 py-2">{m.soil_organic_carbon}</td>
                    <td className="px-4 py-2">{m.biomass}</td>
                    <td className="px-4 py-2">{m.note ?? "—"}</td>
                    <td className="px-4 py-2">
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openEdit(m)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-error-600"
                          onClick={() => handleDelete(m.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <p className="px-4 pt-2 text-xs text-gray-500 dark:text-gray-400">
            Fuente: Gemelo Digital de Humedales · Mediciones de campo · N = {items.length} registros
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
