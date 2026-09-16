"use client";

import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";
import type { LiveValues } from "@/lib/types";
import type { RealtimeConnectionStatus } from "@/lib/realtime";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/lib/i18n";
import { buildSceneParams, type WetlandBaseline } from "./wetlandModel";

const WetlandScene = dynamic(() => import("./WetlandScene"), {
  ssr: false,
  loading: () => <SceneLoading />,
});

function SceneLoading() {
  const { t } = useI18n();
  return (
    <div className="flex h-full w-full items-center justify-center text-sm text-gray-500">
      <Loader2 className="mr-2 h-5 w-5 animate-spin text-brand-500" />
      {t("realtime.twin.loading")}
    </div>
  );
}

const LEGEND = [
  { key: "realtime.twin.legendWater", color: "#2b6cb0" },
  { key: "realtime.twin.legendVegetation", color: "#2f7d32" },
  { key: "realtime.twin.legendCarbon", color: "#12b76a" },
];

export default function WetlandTwinPanel({
  values,
  status,
  baseline,
}: {
  values: LiveValues | null;
  status: RealtimeConnectionStatus;
  baseline?: WetlandBaseline | null;
}) {
  const { t } = useI18n();
  const params = buildSceneParams(values, baseline);
  const active = status === "running";

  return (
    <Card>
      <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle>{t("realtime.twin.title")}</CardTitle>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {t("realtime.twin.desc")}
          </p>
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-300">
          {LEGEND.map((item) => (
            <span key={item.key} className="inline-flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-3 rounded-sm"
                style={{ backgroundColor: item.color }}
              />
              {t(item.key)}
            </span>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-[420px] w-full overflow-hidden rounded-lg border border-gray-200 bg-gray-100 dark:border-gray-800 dark:bg-gray-950">
          <WetlandScene params={params} active={active} />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex flex-wrap gap-4">
            <span>
              {t("realtime.twin.waterTable")}:{" "}
              {values ? values.water_table.toFixed(2) : "—"} m
            </span>
            <span>
              {t("realtime.m.cobertura")}:{" "}
              {values ? `${(values.vegetation_cover * 100).toFixed(1)} %` : "—"}
            </span>
            <span>
              {t("realtime.m.carbon")}:{" "}
              {values ? `${values.retained_carbon.toFixed(1)} tC` : "—"}
            </span>
            <span>
              {t("realtime.m.area")}:{" "}
              {values ? `${values.effective_area_ha.toFixed(1)} ha` : "—"}
            </span>
          </div>
          <span className="italic">{t("realtime.twin.source")}</span>
        </div>
      </CardContent>
    </Card>
  );
}
