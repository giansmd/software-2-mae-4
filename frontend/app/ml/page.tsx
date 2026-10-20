"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getMLMetadata,
  predictML,
  errMessage,
} from "@/lib/api";
import type {
  MLMetadata,
  MLPredictionResult,
  SeaLevelRise,
} from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BrainCircuit, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { ChartExportButtons } from "@/components/ui/chartExportButtons";

const COMPARISON_RESTORATIONS = [0, 20, 40, 60, 80, 90, 100];

interface ComparisonPoint {
  restoration: number;
  ml: number;
  engine: number;
}

interface FormState {
  restoration: number;
  slr: SeaLevelRise;
  horizon: number;
  area: number;
  density: number;
}

const INITIAL_FORM: FormState = {
  restoration: 90,
  slr: "low",
  horizon: 2050,
  area: 120,
  density: 85,
};

function Metric({
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
        <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {label}
        </p>
        <p className="mt-1 text-2xl font-bold">{value}</p>
        {hint && (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{hint}</p>
        )}
      </CardContent>
    </Card>
  );
}

function NumberField({
  label,
  value,
  step = 1,
  onChange,
}: {
  label: string;
  value: number;
  step?: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-gray-600 dark:text-gray-300">{label}</span>
      <input
        type="number"
        value={value}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-900"
      />
    </label>
  );
}

export default function MLPage() {
  const { t } = useI18n();
  const [metadata, setMetadata] = useState<MLMetadata | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [loadingMeta, setLoadingMeta] = useState(true);

  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [comparison, setComparison] = useState<ComparisonPoint[]>([]);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [result, setResult] = useState<MLPredictionResult | null>(null);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);
  const chart1Ref = useRef<HTMLDivElement>(null);
  const chart2Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMLMetadata()
      .then(setMetadata)
      .catch((e) => setMetaError(errMessage(e)))
      .finally(() => setLoadingMeta(false));
  }, []);

  const loadComparison = useCallback(async () => {
    setLoadingComparison(true);
    try {
      const points = await Promise.all(
        COMPARISON_RESTORATIONS.map(async (restoration) => {
          const r = await predictML({
            restoration_level: restoration,
            sea_level_rise: form.slr,
            horizon_year: form.horizon,
            baseline_area_ha: form.area,
            baseline_carbon_density: form.density,
          });
          return {
            restoration,
            ml: r.ml_variation_pct,
            engine: r.engine_variation_pct,
          };
        }),
      );
      setComparison(points);
    } catch {
      setComparison([]);
    } finally {
      setLoadingComparison(false);
    }
  }, [form.slr, form.horizon, form.area, form.density]);

  useEffect(() => {
    loadComparison();
  }, [loadComparison]);

  async function handlePredict() {
    setPredicting(true);
    setPredictError(null);
    try {
      setResult(
        await predictML({
          restoration_level: form.restoration,
          sea_level_rise: form.slr,
          horizon_year: form.horizon,
          baseline_area_ha: form.area,
          baseline_carbon_density: form.density,
        }),
      );
    } catch (e) {
      setPredictError(errMessage(e));
    } finally {
      setPredicting(false);
    }
  }

  const importances = useMemo(() => {
    if (!metadata) return [];
    return Object.entries(metadata.feature_importances)
      .map(([name, value]) => ({
        name: t(`ml.feature.${name}`),
        value: Number((value * 100).toFixed(2)),
      }))
      .sort((a, b) => b.value - a.value);
  }, [metadata, t]);

  if (loadingMeta) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
        <span className="ml-2 text-sm text-gray-500">{t("ml.loading")}</span>
      </div>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-6">
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-6 w-6 text-brand-500" />
          <h1 className="text-3xl font-bold">{t("ml.title")}</h1>
        </div>
        <p className="mt-1 max-w-3xl text-gray-600 dark:text-gray-300">
          {t("ml.subtitle")}
        </p>
      </header>

      {metaError && (
        <div className="mb-4 rounded-md border border-error-300 bg-error-50 p-3 text-sm text-error-700 dark:bg-error-950 dark:text-error-300">
          {t("ml.error")} {metaError}
        </div>
      )}

      {metadata && (
        <>
          <section className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
            <Metric
              label={t("ml.metrics.r2")}
              value={metadata.regression.r2_variation.toFixed(3)}
            />
            <Metric
              label={t("ml.metrics.r2carbon")}
              value={metadata.regression.r2_carbon.toFixed(3)}
            />
            <Metric
              label={t("ml.metrics.mae")}
              value={metadata.regression.mae_variation.toFixed(2)}
            />
            <Metric
              label={t("ml.metrics.accuracy")}
              value={metadata.classification.accuracy.toFixed(3)}
            />
            <Metric
              label={t("ml.metrics.rocAuc")}
              value={metadata.classification.roc_auc.toFixed(3)}
            />
            <Metric
              label={t("ml.metrics.samples")}
              value={metadata.n_samples.toLocaleString()}
              hint={`${metadata.algorithm} · CV R² ${metadata.regression.cv_r2_mean.toFixed(3)}`}
            />
          </section>

          <div className="mb-8 grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle>{t("ml.importance.title")}</CardTitle>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {t("ml.importance.desc")}
                    </p>
                  </div>
                  <ChartExportButtons
                    containerRef={chart1Ref}
                    filename="feature_importance_ml"
                    source="Gemelo Digital · Random Forest"
                    method={metadata?.algorithm ?? "Random Forest"}
                    interpretation="Una importancia mayor indica mayor dependencia predictiva; no demuestra causalidad."
                    params={metadata ? `Muestras: ${metadata.n_samples.toLocaleString()}` : undefined}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div ref={chart1Ref} className="h-[280px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={importances}
                      layout="vertical"
                      margin={{ left: 24, right: 24, bottom: 24 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis
                        type="number"
                        unit="%"
                        label={{ value: "Importancia (%)", position: "insideBottom", offset: -18, fontSize: 12 }}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={140}
                        tick={{ fontSize: 12 }}
                        label={{ value: "Variable", angle: -90, position: "insideLeft", offset: 10, fontSize: 12 }}
                      />
                      <Tooltip formatter={(v) => [`${v}%`, ""]} />
                      <Legend verticalAlign="top" />
                      <Bar dataKey="value" name="Importancia" fill="#465fff" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="mt-2 border-t border-gray-200 pt-2 text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
                  Fuente: {metadata?.data_source ?? "Datos sintéticos del motor"} · Algoritmo: {metadata?.algorithm ?? "Random Forest"} · Entrenado con {metadata?.n_samples.toLocaleString() ?? "—"} muestras
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle>{t("ml.compare.title")}</CardTitle>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {t("ml.compare.desc")}
                    </p>
                  </div>
                  <ChartExportButtons
                    containerRef={chart2Ref}
                    filename="ml_vs_engine_comparison"
                    source="Gemelo Digital · comparación de métodos"
                    method="Motor físico vs Random Forest"
                    interpretation="La distancia entre curvas muestra cuánto difieren las variaciones proyectadas según restauración."
                    params={`SLR: ${form.slr} · Horizonte: ${form.horizon}`}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div ref={chart2Ref} className="h-[280px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={comparison} margin={{ right: 24, bottom: 24 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis
                        dataKey="restoration"
                        unit="%"
                        label={{ value: "Nivel de restauración (%)", position: "insideBottom", offset: -18, fontSize: 12 }}
                      />
                      <YAxis
                        unit="%"
                        label={{ value: "Variación de carbono (%)", angle: -90, position: "insideLeft", offset: 10, fontSize: 12 }}
                      />
                      <Tooltip />
                      <Legend verticalAlign="top" />
                      <Line
                        type="monotone"
                        dataKey="engine"
                        name={t("ml.compare.engine")}
                        stroke="#12b76a"
                        strokeWidth={2.5}
                        dot={false}
                        isAnimationActive={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="ml"
                        name={t("ml.compare.ml")}
                        stroke="#465fff"
                        strokeWidth={2.5}
                        strokeDasharray="5 4"
                        dot={{ r: 3 }}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                {loadingComparison && (
                  <p className="mt-2 text-xs text-gray-400">
                    <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />
                    {t("common.loading")}
                  </p>
                )}
                <p className="mt-2 border-t border-gray-200 pt-2 text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
                  Fuente: Gemelo Digital de Humedales · Comparación: Motor físico determinista vs Emulador ML · Datos: escenarios sintéticos
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("ml.features.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <NumberField
                  label={t("ml.restoration")}
                  value={form.restoration}
                  step={5}
                  onChange={(v) => setForm((f) => ({ ...f, restoration: v }))}
                />
                <label className="flex flex-col gap-1 text-sm">
                  <span className="text-gray-600 dark:text-gray-300">
                    {t("ml.slr")}
                  </span>
                  <select
                    value={form.slr}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        slr: e.target.value as SeaLevelRise,
                      }))
                    }
                    className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-900"
                  >
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                </label>
                <NumberField
                  label={t("ml.horizon")}
                  value={form.horizon}
                  step={5}
                  onChange={(v) => setForm((f) => ({ ...f, horizon: v }))}
                />
                <NumberField
                  label={t("ml.area")}
                  value={form.area}
                  step={10}
                  onChange={(v) => setForm((f) => ({ ...f, area: v }))}
                />
                <NumberField
                  label={t("ml.density")}
                  value={form.density}
                  step={5}
                  onChange={(v) => setForm((f) => ({ ...f, density: v }))}
                />
              </div>

              <div className="mt-4">
                <Button onClick={handlePredict} disabled={predicting}>
                  {predicting && <Loader2 className="h-4 w-4 animate-spin" />}
                  {predicting ? t("ml.predicting") : t("ml.predict")}
                </Button>
              </div>

              {predictError && (
                <p className="mt-3 rounded-md border border-error-300 bg-error-50 p-3 text-sm text-error-700 dark:bg-error-950 dark:text-error-300">
                  {predictError}
                </p>
              )}

              {result && (
                <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
                  <Metric
                    label={t("ml.mlVariation")}
                    value={`${result.ml_variation_pct > 0 ? "+" : ""}${result.ml_variation_pct.toFixed(2)}%`}
                    hint={`P(cumple)=${result.ml_meets_hypothesis_probability.toFixed(2)}`}
                  />
                  <Metric
                    label={t("ml.engineVariation")}
                    value={`${result.engine_variation_pct > 0 ? "+" : ""}${result.engine_variation_pct.toFixed(2)}%`}
                  />
                  <Metric
                    label={t("ml.delta")}
                    value={`${result.delta_variation_pct.toFixed(2)} pp`}
                  />
                  <Metric
                    label={t("ml.mlCarbon")}
                    value={`${result.ml_horizon_carbon.toFixed(1)} t`}
                  />
                  <Metric
                    label={t("ml.engineCarbon")}
                    value={`${result.engine_horizon_carbon.toFixed(1)} t`}
                  />
                  <Card>
                    <CardContent className="flex h-full flex-col justify-center gap-1 p-4 text-sm">
                      <span
                        className={`flex items-center gap-1 font-medium ${
                          result.ml_meets_hypothesis
                            ? "text-success-700 dark:text-success-400"
                            : "text-warning-700 dark:text-warning-400"
                        }`}
                      >
                        {result.ml_meets_hypothesis ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : (
                          <XCircle className="h-4 w-4" />
                        )}
                        {t("ml.mlMeets")} ({result.hypothesis_threshold_pct}%)
                      </span>
                      <span
                        className={`flex items-center gap-1 font-medium ${
                          result.engine_meets_hypothesis
                            ? "text-success-700 dark:text-success-400"
                            : "text-warning-700 dark:text-warning-400"
                        }`}
                      >
                        {result.engine_meets_hypothesis ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : (
                          <XCircle className="h-4 w-4" />
                        )}
                        {t("ml.engineMeets")} ({result.hypothesis_threshold_pct}%)
                      </span>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>

          <p className="mt-6 rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-400">
            {t("ml.dataNotice")} · {t("ml.algo")}: {metadata.algorithm} ·{" "}
            {t("ml.source")}: {metadata.data_source}
          </p>
        </>
      )}
    </main>
  );
}
