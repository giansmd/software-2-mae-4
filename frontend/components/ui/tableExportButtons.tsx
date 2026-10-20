"use client";

import { useRef, useState } from "react";
import { Download, Copy, Check } from "lucide-react";
import { exportTableCsv, copyTableTsv } from "@/lib/tableExport";
import { Button } from "./button";

interface TableExportButtonsProps {
  /** Ref al elemento <table> */
  tableRef: React.RefObject<HTMLTableElement | null>;
  /** Nombre base del archivo (sin extensión) */
  filename: string;
}

/**
 * Botones CSV + Copiar TSV para una tabla.
 * Se coloca junto al título de la tabla.
 */
export function TableExportButtons({
  tableRef,
  filename,
}: TableExportButtonsProps) {
  const [copied, setCopied] = useState(false);

  function handleCsv() {
    if (!tableRef.current) return;
    exportTableCsv(tableRef.current, filename);
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
