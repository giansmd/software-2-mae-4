"use client";

import { useRef, useState } from "react";
import { Download, Copy, Check } from "lucide-react";
import { buildTableNote, exportTableCsv, copyTableTsv } from "@/lib/tableExport";
import { Button } from "./button";

interface TableExportButtonsProps {
  /** Ref al elemento <table> */
  tableRef: React.RefObject<HTMLTableElement | null>;
  /** Nombre base del archivo (sin extensión) */
  filename: string;
  /** Descripción breve de lo que muestran los datos */
  description?: string;
  /** Procedencia de los datos */
  source?: string;
}

/**
 * Botones CSV + Copiar TSV para una tabla.
 * Se coloca junto al título de la tabla.
 */
export function TableExportButtons({
  tableRef,
  filename,
  description = "Datos tabulares exportados desde el Gemelo Digital",
  source = "Gemelo Digital de Humedales",
}: TableExportButtonsProps) {
  const [copied, setCopied] = useState(false);

  function handleCsv() {
    if (!tableRef.current) return;
    const n = Math.max(0, tableRef.current.querySelectorAll("tbody tr").length);
    const note = buildTableNote({ description, source, n });
    exportTableCsv(tableRef.current, filename, note);
  }

  async function handleCopy() {
    if (!tableRef.current) return;
    await copyTableTsv(tableRef.current);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        size="sm"
        variant="outline"
        onClick={handleCsv}
        title="Descargar tabla como CSV (compatible Excel, R, Python)"
      >
        <Download className="h-4 w-4" />
        <span className="ml-1.5">CSV</span>
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={handleCopy}
        title="Copiar tabla al portapapeles (listo para pegar en Excel)"
      >
        {copied ? (
          <>
            <Check className="h-4 w-4 text-success-600" />
            <span className="ml-1.5 text-success-600">Copiado</span>
          </>
        ) : (
          <>
            <Copy className="h-4 w-4" />
            <span className="ml-1.5">Copiar</span>
          </>
        )}
      </Button>
    </div>
  );
}
