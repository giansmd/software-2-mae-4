// Exporta tablas HTML a CSV (universal) y copia al portapapeles como TSV
// (para pegar directamente en Excel / Sheets / Word).

/**
 * Exporta una tabla HTML a CSV UTF-8 con BOM (Excel lo abre bien).
 */
export function exportTableCsv(table: HTMLTableElement, filename: string): void {
  const csv = tableToDelim(table, ",", true);
  // BOM UTF-8 para que Excel detecte la codificación
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  downloadBlob(blob, `${filename}.csv`);
}

/**
 * Copia la tabla al portapapeles como TSV (listo para pegar en Excel).
 */
export async function copyTableTsv(table: HTMLTableElement): Promise<void> {
  const tsv = tableToDelim(table, "\t", false);
  await navigator.clipboard.writeText(tsv);
}

function tableToDelim(
  table: HTMLTableElement,
  delim: string,
  quoteCsv: boolean,
): string {
  const rows: string[] = [];
  table.querySelectorAll("tr").forEach((tr) => {
    const cells: string[] = [];
    tr.querySelectorAll("th, td").forEach((cell) => {
      // Saltar columna de acciones (última th/td con botones)
      if (cell.querySelector("button")) return;
      const text = (cell.textContent ?? "").trim().replace(/\s+/g, " ");
      cells.push(quoteCsv ? csvEscape(text, delim) : text);
    });
    rows.push(cells.join(delim));
  });
  return rows.join("\n");
}

function csvEscape(value: string, delim: string): string {
  if (value.includes(delim) || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Construye la nota de interpretabilidad para una tabla.
 */
export function buildTableNote(parts: {
  description: string;
  source: string;
  n?: number;
  date?: string;
}): string {
  const date = parts.date ?? new Date().toISOString().slice(0, 10);
  const nPart = parts.n !== undefined ? ` · N = ${parts.n}` : "";
  return `${parts.description} · Fuente: ${parts.source}${nPart} · Fecha: ${date}`;
}
