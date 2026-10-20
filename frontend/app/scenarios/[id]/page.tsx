"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { runSimulation, getScenario, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  PredictionMethod,
  Scenario,
  SeaLevelRise,
  SimulationResult,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CheckCircle2, XCircle, Loader2, ArrowLeft } from "lucide-react";
import { ChartExportButtons } from "@/components/ui/chartExportButtons";

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {label}
        </p>
        <p className="mt-1 text-2xl font-bold">{value}</p>
        {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default function ScenarioPage() {
  const { t } = useI18n();
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const { isAuthed, loading: authLoading } = useAuth();

  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [restoration_level, setRestorationLevel] = useState(50);
  const [sea_level_rise, setSeaLevelRise] = useState<SeaLevelRise>("medium");
  const [horizon_year, setHorizonYear] = useState(2050);
  const [baseline_area_ha, setBaselineArea] = useState(100);
  const [baseline_carbon_density, setBaselineCarbon] = useState(50);
  const [method, setMethod] = useState<PredictionMethod>("engine");
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chart1Ref = useRef<HTMLDivElement>(null);
  const chart2Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthed) {
      router.push("/login");
      return;
    }
    setLoading(true);
    getScenario(id)
      .then((s) => {
        setScenario(s);
        setRestorationLevel(s.restoration_level);
        setSeaLevelRise(s.sea_level_rise);
        setHorizonYear(s.horizon_year);
        setBaselineArea(s.baseline_area_ha);
        setBaselineCarbon(s.baseline_carbon_density);
      })
      .catch((e) => {
        const ae = e as ApiError;
        if (ae?.status === 401) router.push("/login");
        else setError(String(ae?.message ?? e));
      })
      .finally(() => setLoading(false));
  }, [authLoading, isAuthed, id, router]);

  async function handleSimulate() {
    if (!isAuthed) {
      router.push("/login");
      return;
    }
    setSimulating(true);
    setError(null);
    try {
      const r = await runSimulation({
        restoration_level,
        sea_level_rise,
        horizon_year,
        baseline_area_ha,
        baseline_carbon_density,
        scenario_name: scenario?.name,
        method,
      });
      setResult(r);
    } catch (e) {
      setError(String((e as ApiError)?.message ?? e));
    } finally {
      setSimulating(false);
    }
  }

  if (loading || authLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <Link
        href="/scenarios"
        className="mb-4 inline-flex items-center gap-1 text-sm text-gray-500 hover:underline"
      >
        <ArrowLeft className="h-4 w-4" /> Volver a escenarios
      </Link>
      <h1 className="mb-1 text-3xl font-bold">
        Simulación: {scenario?.name}
      </h1>
      <p className="mb-6 text-gray-600 dark:text-gray-300">
        Ajusta los parámetros y simula la proyección de retención de carbono.
      </p>

      {error && (
        <div className="mb-4 rounded-md border border-error-300 bg-error-50 p-3 text-sm text-error-700 dark:bg-error-950 dark:text-error-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("scenarios.parametros")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="block text-sm">
              Nivel de restauración: {restoration_level}%
              <input
                type="range"
                min={0}
                max={100}
                value={restoration_level}
                onChange={(e) => setRestorationLevel(Number(e.target.value))}
                className="w-full"
              />
            </label>
            <label className="block text-sm">
              Aumento nivel del mar
              <select
                value={sea_level_rise}
                onChange={(e) =>
                  setSeaLevelRise(e.target.value as SeaLevelRise)
                }
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              >
                <option value="low">Bajo</option>
                <option value="medium">Medio</option>
                <option value="high">Alto</option>
              </select>
            </label>
            <label className="block text-sm">
              Año horizonte
              <input
                type="number"
                value={horizon_year}
                onChange={(e) => setHorizonYear(Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
            </label>
            <label className="block text-sm">
              Superficie base (ha)
              <input
                type="number"
                value={baseline_area_ha}
                onChange={(e) => setBaselineArea(Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
            </label>
            <label className="block text-sm">
              Densidad carbono base (t/ha)
              <input
                type="number"
                value={baseline_carbon_density}
                onChange={(e) =>
                  setBaselineCarbon(Number(e.target.value))
                }
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
            </label>
            <label className="block text-sm">
              {t("method.label")}
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as PredictionMethod)}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              >
                <option value="engine">{t("method.engine")}</option>
                <option value="ml">{t("method.ml")}</option>
                <option value="ensemble">{t("method.ensemble")}</option>
              </select>
            </label>
            <Button className="w-full" onClick={handleSimulate} disabled={simulating}>
              {simulating && <Loader2 className="h-4 w-4 animate-spin" />}
              Simular
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {result && (
            <>
              <div
                className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium ${
                  result.meets_hypothesis
                    ? "bg-success-100 text-success-800 dark:bg-success-900 dark:text-success-200"
                    : "bg-warning-100 text-warning-800 dark:bg-warning-900 dark:text-warning-200"
                }`}
              >
                {result.meets_hypothesis ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : (
                  <XCircle className="h-5 w-5" />
                )}
                {result.meets_hypothesis
                  ? `Cumple la hipótesis: +${result.horizon_variation_pct.toFixed(1)}% (umbral ${result.hypothesis_threshold_pct}%)`
                  : `No cumple la hipótesis: ${result.horizon_variation_pct.toFixed(1)}% (umbral ${result.hypothesis_threshold_pct}%)`}
              </div>

              {result.ml_horizon_variation_pct !== null && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t(`method.${result.method}`)} ·{" "}
                  {t("method.compare", {
                    engine: result.engine_horizon_variation_pct.toFixed(1),
                    ml: result.ml_horizon_variation_pct.toFixed(1),
                  })}
                </p>
              )}

              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Kpi label="Carbono base" value={`${result.baseline_carbon.toFixed(1)} t`} />
                <Kpi label="Carbono horizonte" value={`${result.horizon_carbon.toFixed(1)} t`} />
                <Kpi
                  label="Variación"
                  value={`${result.horizon_variation_pct > 0 ? "+" : ""}${result.horizon_variation_pct.toFixed(1)}%`}
                />
                <Kpi
                  label="Superficie efectiva"
                  value={`${result.series[result.series.length - 1]?.effective_area_ha.toFixed(1) ?? "-"} ha`}
                />
              </div>

              <Card>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle>{t("scenarios.chartSerie")}</CardTitle>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Proyección anual de carbono retenido y superficie efectiva bajo el escenario configurado.
                      </p>
                    </div>
                    <ChartExportButtons
                      containerRef={chart1Ref}
                      filename={`serie_carbono_${scenario?.id ?? "scenario"}`}
                      source="Gemelo Digital · simulación"
                      method={t(`method.${result.method}`)}
                      params={`Restauración: ${restoration_level}% · SLR: ${sea_level_rise} · Horizonte: ${horizon_year}`}
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <div ref={chart1Ref} className="h-[340px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={result.series} margin={{ left: 8, right: 16, top: 8, bottom: 24 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                        <XAxis
                          dataKey="year"
                          label={{ value: "Año", position: "insideBottom", offset: -18, fontSize: 12 }}
                        />
                        <YAxis
                          label={{ value: "Carbono (t) / Superficie (ha)", angle: -90, position: "insideLeft", offset: 10, fontSize: 11 }}
                        />
                        <Tooltip />
                        <Legend verticalAlign="top" />
                        <Line
                          type="monotone"
                          dataKey="retained_carbon"
                          name="Carbono retenido (t)"
                          stroke="#12b76a"
                          strokeWidth={2}
                          dot={false}
                        />
                        <Line
                          type="monotone"
                          dataKey="effective_area_ha"
                          name="Superficie efectiva (ha)"
                          stroke="#465fff"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="mt-2 border-t border-gray-200 pt-2 text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
                    Fuente: Gemelo Digital de Humedales · Método: {t(`method.${result.method}`)} · Escenario: {scenario?.name}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <CardTitle>{t("scenarios.chartCobertura")}</CardTitle>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Evolución anual de la cobertura vegetal efectiva del humedal.
                      </p>
                    </div>
                    <ChartExportButtons
                      containerRef={chart2Ref}
                      filename={`cobertura_${scenario?.id ?? "scenario"}`}
                      source="Gemelo Digital · simulación"
                      method={t(`method.${result.method}`)}
                      params={`Restauración: ${restoration_level}% · SLR: ${sea_level_rise} · Horizonte: ${horizon_year}`}
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <div ref={chart2Ref} className="h-[260px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={result.series} margin={{ left: 8, right: 16, top: 8, bottom: 24 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                        <XAxis
                          dataKey="year"
                          label={{ value: "Año", position: "insideBottom", offset: -18, fontSize: 12 }}
                        />
                        <YAxis
                          label={{ value: "Cobertura (%)", angle: -90, position: "insideLeft", offset: 10, fontSize: 12 }}
                        />
                        <Tooltip />
                        <Legend verticalAlign="top" />
                        <Bar
                          dataKey="vegetation_cover"
                          name="Cobertura (%)"
                          fill="#12b76a"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="mt-2 border-t border-gray-200 pt-2 text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
                    Fuente: Gemelo Digital de Humedales · Método: {t(`method.${result.method}`)} · Escenario: {scenario?.name}
                  </p>
                </CardContent>
              </Card>
            </>
          )}

          {!result && !simulating && (
            <Card>
              <CardContent className="p-10 text-center text-gray-500">
                Ajusta los parámetros y pulsa «Simular» para ver la proyección.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}
