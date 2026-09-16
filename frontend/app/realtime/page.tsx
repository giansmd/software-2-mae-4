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
import WetlandTwinPanel from "@/components/twin/WetlandTwinPanel";
import { useI18n } from "@/lib/i18n";

const STATUS_LABELS_ES: Record<RealtimeConnectionStatus, string> = {
  connecting: "Conectando",
  running: "Ejecutando",
  paused: "Pausado",
  completed: "Horizonte alcanzado",
  disconnected: "Desconectado",
};
const STATUS_LABELS_EN: Record<RealtimeConnectionStatus, string> = {
  connecting: "Connecting",
  running: "Running",
  paused: "Paused",
  completed: "Horizon reached",
  disconnected: "Disconnected",
};

function formatTime(value: string) {
  return value.slice(0, 10);
}

function Metric({ label, value, unit, accent = "text-gray-900 dark:text-white" }: {
  label: string;
  value: string;
  unit: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{label}</p>
      <p className={`mt-2 text-2xl font-bold ${accent}`}>{value}</p>
      <p className="text-xs text-gray-500">{unit}</p>
    </div>
  );
}

export default function RealtimePage() {
  const { t, lang } = useI18n();
  const STATUS_LABELS = lang === "en" ? STATUS_LABELS_EN : STATUS_LABELS_ES;
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
    return <main className="mx-auto max-w-7xl px-4 py-12 text-center text-gray-500">{t("common.loading")}</main>;
  }

  if (loadError) {
    return <main className="mx-auto max-w-7xl px-4 py-12"><p className="rounded-lg border border-error-200 bg-error-50 p-4 text-error-700">{loadError}</p></main>;
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-brand-600 dark:text-brand-400">
            <Activity className="h-4 w-4" /> {t("realtime.centro")}
          </div>
          <h1 className="text-3xl font-bold tracking-tight">{t("realtime.titulo")}</h1>
          <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-300">
            {t("realtime.desc")}
          </p>
        </div>
        <div className={`inline-flex items-center gap-2 self-start rounded-full px-3 py-1.5 text-sm font-medium md:self-auto ${realtime.status === "running" ? "bg-success-100 text-success-800 dark:bg-success-950 dark:text-success-300" : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"}`}>
          {realtime.status === "disconnected" ? <WifiOff className="h-4 w-4" /> : <Wifi className="h-4 w-4" />}
          {STATUS_LABELS[realtime.status]}
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>{t("realtime.escenario")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {scenarios.length === 0 ? (
              <p className="text-sm text-gray-500">{t("realtime.noEscenariosPub")}</p>
            ) : (
              <>
                <label className="block text-sm font-medium">
                  {t("realtime.humedalRef")}
                  <select
                    value={scenarioId ?? ""}
                    onChange={(event) => setScenarioId(Number(event.target.value))}
                    className="mt-2 w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
                  >
                    {scenarios.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </label>
                {scenario && (
                  <div className="space-y-2 rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-950">
                    <p className="font-medium">{scenario.name}</p>
                    <p className="text-gray-500">{t("realtime.restauracion", { pct: scenario.restoration_level })}</p>
                    <p className="text-gray-500">{t("realtime.slr", { v: scenario.sea_level_rise })}</p>
                    <p className="text-gray-500">{t("realtime.horizonte", { v: scenario.horizon_year })}</p>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={realtime.start} disabled={realtime.status === "running" || realtime.status === "connecting"}>
                    <Play className="h-4 w-4" /> {t("realtime.iniciar")}
                  </Button>
                  <Button size="sm" variant="outline" onClick={realtime.pause} disabled={realtime.status !== "running"}>
                    <Pause className="h-4 w-4" /> {t("realtime.pausar")}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={realtime.reset}>
                    <RotateCcw className="h-4 w-4" /> {t("realtime.reiniciar")}
                  </Button>
                </div>
                <label className="block text-sm font-medium">
                  {t("realtime.velocidad")}
                  <select
                    defaultValue="4"
                    onChange={(event) => realtime.setSpeed(Number(event.target.value))}
                    className="mt-2 w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
                  >
                    <option value="1">1x</option>
                    <option value="4">4x</option>
                    <option value="10">10x</option>
                    <option value="20">20x</option>
                  </select>
                </label>
              </>
            )}
            <p className="border-t border-gray-200 pt-4 text-xs leading-relaxed text-gray-500 dark:border-gray-800">
              {t("realtime.fuente")}
            </p>
          </CardContent>
        </Card>

        <section className="space-y-6">
          {realtime.error && <p className="rounded-lg border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800">{realtime.error}</p>}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Metric label={t("realtime.m.carbon")} value={current ? current.retained_carbon.toFixed(1) : "—"} unit="tC" accent="text-success-600 dark:text-success-400" />
            <Metric label={t("realtime.m.freatico")} value={current ? current.water_table.toFixed(2) : "—"} unit="m" accent="text-brand-700 dark:text-brand-400" />
            <Metric label={t("realtime.m.cobertura")} value={current ? `${(current.vegetation_cover * 100).toFixed(1)}` : "—"} unit="%" accent="text-blue-light-700 dark:text-blue-light-400" />
            <Metric label={t("realtime.m.area")} value={current ? current.effective_area_ha.toFixed(1) : "—"} unit="ha" accent="text-warning-700 dark:text-warning-400" />
          </div>

          <WetlandTwinPanel
            values={current}
            status={realtime.status}
            baseline={
              scenario
                ? {
                    areaHa: scenario.baseline_area_ha,
                    carbonDensity: scenario.baseline_carbon_density,
                  }
                : null
            }
          />

          <Card>
            <CardHeader>
              <CardTitle>{t("realtime.chartCS")}</CardTitle>
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
                    <Line yAxisId="carbon" type="monotone" dataKey="retained_carbon" name={t("realtime.chartCSline")} stroke="#12b76a" strokeWidth={2.5} dot={false} />
                    <Line yAxisId="area" type="monotone" dataKey="effective_area_ha" name={t("realtime.chartCSarea")} stroke="#465fff" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>{t("realtime.chartFreatico")}</CardTitle></CardHeader>
              <CardContent>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={realtime.points} margin={{ left: 8, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="time" tickFormatter={formatTime} minTickGap={32} />
                      <YAxis />
                      <Tooltip labelFormatter={(value) => formatTime(String(value))} />
                      <Line type="monotone" dataKey="water_table" name={t("realtime.chartFreaticoLine")} stroke="#465fff" strokeWidth={2.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>{t("realtime.chartCobertura")}</CardTitle></CardHeader>
              <CardContent>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={realtime.points} margin={{ left: 8, right: 16 }}>
                      <defs><linearGradient id="coverFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#12b76a" stopOpacity={0.35} /><stop offset="95%" stopColor="#12b76a" stopOpacity={0} /></linearGradient></defs>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="time" tickFormatter={formatTime} minTickGap={32} />
                      <YAxis tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} domain={[0, 1]} />
                      <Tooltip formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, t("realtime.chartCoberturaName")]} labelFormatter={(value) => formatTime(String(value))} />
                      <Area type="monotone" dataKey="vegetation_cover" name={t("realtime.chartCoberturaName")} stroke="#12b76a" fill="url(#coverFill)" strokeWidth={2.5} />
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
