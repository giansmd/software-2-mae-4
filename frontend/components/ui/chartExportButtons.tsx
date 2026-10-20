"use client";

import { useRef, useState } from "react";
import { Download, FileImage, FileText } from "lucide-react";
import { exportChartPng, exportChartSvg, buildNote } from "@/lib/chartExport";
import { Button } from "./button";

interface ChartExportButtonsProps {
  /** Ref al contenedor que envuelve el ResponsiveContainer */
  containerRef: React.RefObject<HTMLDivElement | null>;
  /** Nombre base del archivo (sin extensión) */
  filename: string;
  /** Fuente de los datos */
  source: string;
  /** Método usado */
  method?: string;
  /** Parámetros adicionales como texto */
  params?: string;
  /** Fecha (por defecto hoy ISO) */
  date?: string;
}

/**
 * Botones PNG 600 DPI + SVG vectorial para un gráfico.
 * Se coloca junto al título del Card.
 */
export function ChartExportButtons({
  containerRef,
  filename,
  source,
  method,
  params,
  date,
}: ChartExportButtonsProps) {
  const [busy, setBusy] = useState<null | "png" | "svg">(null);
  const [error, setError] = useState<string | null>(null);

  async function handlePng() {
    if (!containerRef.current) return;
    setBusy("png");
    setError(null);
    try {
      const note = buildNote({ source, method, params, date });
      await exportChartPng(containerRef.current, filename, note);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  function handleSvg() {
    if (!containerRef.current) return;
    try {
      exportChartSvg(containerRef.current, filename);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        size="sm"
        variant="outline"
        onClick={handlePng}
        disabled={busy !== null}
        title="Descargar figura como PNG a 600 DPI"
      >
        {busy === "png" ? (
          <FileImage className="h-4 w-4 animate-pulse" />
        ) : (
          <Download className="h-4 w-4" />
        )}
        <span className="ml-1.5">PNG 600dpi</span>
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={handleSvg}
        title="Descargar figura como SVG vectorial"
      >
        <FileText className="h-4 w-4" />
        <span className="ml-1.5">SVG</span>
      </Button>
      {error && <span className="text-xs text-error-600">{error}</span>}
    </div>
  );
}
