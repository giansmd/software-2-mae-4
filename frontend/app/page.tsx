"use client";

import { useEffect, useMemo, useState } from "react";
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
} from "recharts";
import {
  getScenarios,
  getSimulation,
  runSimulation,
  errMessage,
} from "@/lib/api";
import type { Scenario, SimulationResult } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useI18n } from "@/lib/i18n";

const HYPOTHESIS_PCT = 25;

function Kpi({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <p className="mt-1 text-2xl font-bold">{value}</p>
        {hint && (
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {hint}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { t } = useI18n();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [results, setResults] = useState<Record<number, SimulationResult>>({});
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getScenarios()
      .then((data) => {
        setScenarios(data);
        const pub = data.filter((s) => s.is_public).map((s) => s.id);
        setSelected(pub.slice(0, 3));
      })
      .catch((e) => setError(errMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  async function simulate(ids: number[]) {
    setSimulating(true);
    setError(null);
    const map: Record<number, SimulationResult> = {};
    try {
      await Promise.all(
        ids.map(async (id) => {
          try {
            map[id] = await getSimulation(id);
          } catch {
            const sc = scenarios.find((s) => s.id === id);
            if (sc) {
              map[id] = await runSimulation({ scenario_id: id });
            }
          }
        }),
      );
      setResults(map);
    } catch (e) {
      setError(errMessage(e));
    } finally {
      setSimulating(false);
    }
  }

  useEffect(() => {
    if (selected.length) simulate(selected);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected.join(",")]);

  const chartData = useMemo(() => {
    const allYears = new Set<number>();
    Object.values(results).forEach((r) =>
      r.series.forEach((p) => allYears.add(p.year)),
    );
    const years = Array.from(allYears).sort((a, b) => a - b);
    return years.map((year) => {
      const row: Record<string, number> = { year };
      Object.entries(results).forEach(([id, r]) => {
        const pt = r.series.find((p) => p.year === year);
        if (pt) row[`c_${id}`] = pt.retained_carbon;
      });
      return row;
    });
  }, [results]);

  const colors = ["#059669", "#2563eb", "#d97706", "#9333ea", "#dc2626"];

  function toggle(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  const selectedScenarios = scenarios.filter((s) =>
    selected.includes(s.id),
  );

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">{t("app.title")}</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-300">
          {t("dash.subtitle", { pct: HYPOTHESIS_PCT })}
        </p>
        <Link
          href="/realtime"
          className="mt-4 inline-flex rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          {t("dash.openRealtime")}
        </Link>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <section className="mb-8">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          {t("dash.publicScenarios")}
        </h2>
        {scenarios.length === 0 ? (
          <p className="text-sm text-slate-500">
            {t("dash.noScenarios")}
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {scenarios.map((s) => (
              <button
                key={s.id}
                onClick={() => toggle(s.id)}
                className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                  selected.includes(s.id)
                    ? "border-emerald-600 bg-emerald-600 text-white"
                    : "border-slate-300 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                }`}
              >
                {s.name}
              </button>
            ))}
          </div>
        )}
      </section>

      {simulating && (
        <div className="mb-4 flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> {t("dash.simulating")}
        </div>
      )}

      {selectedScenarios.map((s) => {
        const r = results[s.id];
        if (!r) return null;
        return (
          <div key={s.id} className="mb-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{r.scenario_name}</CardTitle>
                  <span
                    className={`flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium ${
                      r.meets_hypothesis
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200"
                        : "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                    }`}
                  >
                    {r.meets_hypothesis ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <XCircle className="h-4 w-4" />
                    )}
                    {r.meets_hypothesis
                      ? t("dash.meetsHypothesis", { pct: r.hypothesis_threshold_pct })
                      : t("dash.notMeets", { pct: r.hypothesis_threshold_pct })}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <Kpi
                    label={t("dash.carbonBase")}
                    value={`${r.baseline_carbon.toFixed(1)} t`}
                  />
                  <Kpi
                    label={t("dash.carbonHorizon")}
                    value={`${r.horizon_carbon.toFixed(1)} t`}
                  />
                  <Kpi
                    label={t("dash.variation")}
                    value={`${r.horizon_variation_pct > 0 ? "+" : ""}${r.horizon_variation_pct.toFixed(1)}%`}
                    hint={t("dash.threshold", { pct: r.hypothesis_threshold_pct })}
                  />
                  <Kpi
                    label={t("dash.effectiveArea")}
                    value={`${r.series[r.series.length - 1]?.effective_area_ha.toFixed(1) ?? "-"} ha`}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        );
      })}

      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("dash.projectedChart")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[360px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="year" />
                  <YAxis
                    label={{
                      value: t("dash.yLabel"),
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip />
                  <Legend />
                  {selectedScenarios.map((s, i) => (
                    <Line
                      key={s.id}
                      type="monotone"
                      dataKey={`c_${s.id}`}
                      name={s.name}
                      stroke={colors[i % colors.length]}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="mt-8 text-center text-sm text-slate-500">
        {t("dash.researcherCtaPrefix")}{" "}
        <a href="/login" className="text-emerald-600 underline">
          {t("dash.loginLink")}
        </a>{" "}
        {t("dash.researcherCtaSuffix")}
      </div>
    </main>
  );
}
