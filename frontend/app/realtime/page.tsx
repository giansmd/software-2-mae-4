"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, Pause, Play, RotateCcw, Wifi, WifiOff } from "lucide-react";
import { getScenarios, errMessage } from "@/lib/api";
import { useRealtimeSimulation, type RealtimeConnectionStatus } from "@/lib/realtime";
import type { Scenario } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STATUS_LABELS: Record<RealtimeConnectionStatus, string> = {
  connecting: "Conectando",
  running: "Ejecutando",
  paused: "Pausado",
  completed: "Horizonte alcanzado",
  disconnected: "Desconectado",
};

function formatTime(value: string) {
  return value.slice(0, 10);
}

function Metric({ label, value, unit, accent = "text-slate-900 dark:text-white" }: {
  label: string;
  value: string;
  unit: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${accent}`}>{value}</p>
      <p className="text-xs text-slate-500">{unit}</p>
    </div>
  );
}

export default function RealtimePage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenarioId, setScenarioId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const realtime = useRealtimeSimulation(scenarioId);
  const scenario = scenarios.find((item) => item.id === scenarioId);
  const current = realtime.lastPoint;

  useEffect(() => {
    getScenarios()
      .then((items) => {
        const publicScenarios = items.filter((item) => item.is_public);
        setScenarios(publicScenarios);
        setScenarioId(publicScenarios[0]?.id ?? null);
      })
      .catch((error) => setLoadError(errMessage(error)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <main className="mx-auto max-w-7xl px-4 py-12 text-center text-slate-500">Cargando escenarios…</main>;
  }

  if (loadError) {
    return <main className="mx-auto max-w-7xl px-4 py-12"><p className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{loadError}</p></main>;
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
            <Activity className="h-4 w-4" /> Centro de monitoreo
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Estado del humedal en vivo</h1>
          <p className="mt-2 max-w-2xl text-slate-600 dark:text-slate-300">
            Observa cómo evoluciona el humedal con el escenario seleccionado. Esta primera versión utiliza una señal simulada reproducible.
          </p>
        </div>
        <div className={`inline-flex items-center gap-2 self-start rounded-full px-3 py-1.5 text-sm font-medium md:self-auto ${realtime.status === "running" ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"}`}>
          {realtime.status === "disconnected" ? <WifiOff className="h-4 w-4" /> : <Wifi className="h-4 w-4" />}
          {STATUS_LABELS[realtime.status]}
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Escenario</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {scenarios.length === 0 ? (
              <p className="text-sm text-slate-500">No hay escenarios públicos disponibles.</p>
            ) : (
              <>
                <label className="block text-sm font-medium">
                  Humedal de referencia
                  <select
                    value={scenarioId ?? ""}
                    onChange={(event) => setScenarioId(Number(event.target.value))}
                    className="mt-2 w-full rounded-md border border-slate-300 bg-transparent px-3 py-2 text-sm dark:border-slate-700"
                  >
                    {scenarios.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </label>
                {scenario && (
                  <div className="space-y-2 rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-950">
                    <p className="font-medium">{scenario.name}</p>
                    <p className="text-slate-500">Restauración: {scenario.restoration_level}%</p>
                    <p className="text-slate-500">SLR: {scenario.sea_level_rise}</p>
                    <p className="text-slate-500">Horizonte: {scenario.horizon_year}</p>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={realtime.start} disabled={realtime.status === "running" || realtime.status === "connecting"}>
                    <Play className="h-4 w-4" /> Iniciar
                  </Button>
                  <Button size="sm" variant="outline" onClick={realtime.pause} disabled={realtime.status !== "running"}>
                    <Pause className="h-4 w-4" /> Pausar
                  </Button>
                  <Button size="sm" variant="ghost" onClick={realtime.reset}>
                    <RotateCcw className="h-4 w-4" /> Reiniciar
                  </Button>
                </div>
                <label className="block text-sm font-medium">
                  Velocidad
                  <select
                    defaultValue="4"
                    onChange={(event) => realtime.setSpeed(Number(event.target.value))}
                    className="mt-2 w-full rounded-md border border-slate-300 bg-transparent px-3 py-2 text-sm dark:border-slate-700"
                  >
                    <option value="1">1x</option>
                    <option value="4">4x</option>
                    <option value="10">10x</option>
                    <option value="20">20x</option>
                  </select>
                </label>
              </>
            )}
            <p className="border-t border-slate-200 pt-4 text-xs leading-relaxed text-slate-500 dark:border-slate-800">
              Fuente actual: <strong>simulada</strong>. Los valores representan una reproducción del horizonte del escenario, no lecturas de sensores.
            </p>
          </CardContent>
        </Card>

        <section className="space-y-6">
          {realtime.error && <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">{realtime.error}</p>}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric label="Carbono retenido" value={current ? current.retained_carbon.toFixed(1) : "—"} unit="tC" accent="text-emerald-700 dark:text-emerald-400" />
            <Metric label="Nivel freático" value={current ? current.water_table.toFixed(2) : "—"} unit="m" accent="text-blue-700 dark:text-blue-400" />
            <Metric label="Cobertura vegetal" value={current ? `${(current.vegetation_cover * 100).toFixed(1)}` : "—"} unit="%" accent="text-teal-700 dark:text-teal-400" />
            <Metric label="Superficie efectiva" value={current ? current.effective_area_ha.toFixed(1) : "—"} unit="ha" accent="text-amber-700 dark:text-amber-400" />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Carbono y superficie</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[320px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={realtime.points} margin={{ left: 8, right: 16, top: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="time" tickFormatter={formatTime} minTickGap={32} />
                    <YAxis yAxisId="carbon" />
                    <YAxis yAxisId="area" orientation="right" />
                    <Tooltip labelFormatter={(value) => formatTime(String(value))} />
                    <Line yAxisId="carbon" type="monotone" dataKey="retained_carbon" name="Carbono retenido (tC)" stroke="#059669" strokeWidth={2.5} dot={false} />
                    <Line yAxisId="area" type="monotone" dataKey="effective_area_ha" name="Superficie efectiva (ha)" stroke="#2563eb" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Nivel freático</CardTitle></CardHeader>
              <CardContent>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={realtime.points} margin={{ left: 8, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="time" tickFormatter={formatTime} minTickGap={32} />
                      <YAxis />
                      <Tooltip labelFormatter={(value) => formatTime(String(value))} />
                      <Line type="monotone" dataKey="water_table" name="Nivel de agua (m)" stroke="#2563eb" strokeWidth={2.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Cobertura vegetal</CardTitle></CardHeader>
              <CardContent>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={realtime.points} margin={{ left: 8, right: 16 }}>
                      <defs><linearGradient id="coverFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.35} /><stop offset="95%" stopColor="#10b981" stopOpacity={0} /></linearGradient></defs>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="time" tickFormatter={formatTime} minTickGap={32} />
                      <YAxis tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} domain={[0, 1]} />
                      <Tooltip formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, "Cobertura"]} labelFormatter={(value) => formatTime(String(value))} />
                      <Area type="monotone" dataKey="vegetation_cover" name="Cobertura" stroke="#059669" fill="url(#coverFill)" strokeWidth={2.5} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
}
