import { toPng } from "html-to-image";

const DPI_TARGET = 600;
const DPI_SCREEN = 96;
const PIXEL_RATIO = DPI_TARGET / DPI_SCREEN;

export async function exportChartPng(
  container: HTMLElement,
  filename: string,
  note?: string,
): Promise<void> {
  const { width, height } = container.getBoundingClientRect();
  if (!width || !height) throw new Error("El gráfico aún no tiene dimensiones visibles");

  const dataUrl = await toPng(container, {
    backgroundColor: "#ffffff",
    cacheBust: true,
    pixelRatio: PIXEL_RATIO,
    skipAutoScale: true,
    width,
    height,
  });
  const chart = await loadImage(dataUrl);
  const scale = chart.width / width;
  const padding = Math.round(12 * scale);
  const lineHeight = Math.round(16 * scale);
  const fontSize = Math.round(11 * scale);
  const measureCanvas = document.createElement("canvas");
  const measureContext = measureCanvas.getContext("2d");
  if (!measureContext) throw new Error("No se pudo crear el canvas");
  measureContext.font = `${fontSize}px Arial, sans-serif`;
  const lines = note ? wrapText(measureContext, note, chart.width - padding * 2) : [];
  const noteHeight = lines.length ? lines.length * lineHeight + padding * 2 : 0;
  const canvas = document.createElement("canvas");
  canvas.width = chart.width;
  canvas.height = chart.height + noteHeight;

  const context = canvas.getContext("2d");
  if (!context) throw new Error("No se pudo crear el canvas");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(chart, 0, 0);

  if (note) {
    context.fillStyle = "#4b5563";
    context.font = `${fontSize}px Arial, sans-serif`;
    context.textBaseline = "top";
    lines.forEach((line, index) => {
      context.fillText(line, padding, chart.height + padding + index * lineHeight);
    });
  }

  const png = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("No se pudo generar el PNG"))), "image/png");
  });
  downloadBlob(await setPngDpi(png, DPI_TARGET), `${filename}.png`);
}

export function exportChartSvg(container: HTMLElement, filename: string, note?: string): void {
  const svg = container.querySelector("svg");
  if (!svg) throw new Error("SVG no encontrado en el contenedor");

  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  const viewBox = (clone.getAttribute("viewBox") ?? `0 0 ${svg.clientWidth} ${svg.clientHeight}`)
    .trim().split(/\s+/).map(Number);
  const [x, y, width, height] = viewBox;
  const noteLines = note ? wrapSvgText(note, 105) : [];
  const footerHeight = noteLines.length ? noteLines.length * 16 + 12 : 0;
  clone.setAttribute("width", String(width));
  clone.setAttribute("height", String(height + footerHeight));
  if (note) {
    clone.setAttribute("viewBox", `${x} ${y} ${width} ${height + footerHeight}`);
    const footer = document.createElementNS("http://www.w3.org/2000/svg", "text");
    footer.setAttribute("x", String(x + 8));
    footer.setAttribute("y", String(y + height + 18));
    footer.setAttribute("font-size", "11");
    footer.setAttribute("font-family", "Arial, sans-serif");
    footer.setAttribute("fill", "#4b5563");
    noteLines.forEach((line, index) => {
      const span = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      span.setAttribute("x", String(x + 8));
      span.setAttribute("dy", index === 0 ? "0" : "14");
      span.textContent = line;
      footer.appendChild(span);
    });
    clone.appendChild(footer);
  }

  const blob = new Blob([new XMLSerializer().serializeToString(clone)], {
    type: "image/svg+xml;charset=utf-8",
  });
  downloadBlob(blob, `${filename}.svg`);
}

export function buildNote(parts: {
  source: string;
  method?: string;
  interpretation?: string;
  date?: string;
  params?: string;
}): string {
  return [
    `Fuente: ${parts.source}`,
    parts.method && `Método: ${parts.method}`,
    parts.interpretation && `Interpretación: ${parts.interpretation}`,
    parts.params,
    `Fecha: ${parts.date ?? new Date().toISOString().slice(0, 10)}`,
  ].filter(Boolean).join(" · ");
}

function wrapText(context: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (line && context.measureText(next).width > maxWidth) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function wrapSvgText(text: string, maxLength: number): string[] {
  const lines: string[] = [];
  let line = "";
  for (const word of text.split(/\s+/)) {
    const next = line ? `${line} ${word}` : word;
    if (line && next.length > maxLength) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("No se pudo cargar el gráfico exportado"));
    image.src = src;
  });
}

async function setPngDpi(blob: Blob, dpi: number): Promise<Blob> {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  const ppm = Math.round(dpi / 0.0254);
  const data = new Uint8Array(9);
  const view = new DataView(data.buffer);
  view.setUint32(0, ppm);
  view.setUint32(4, ppm);
  data[8] = 1;
  const chunk = createPngChunk("pHYs", data);
  const chunks: Uint8Array[] = [bytes.slice(0, 8)];
  let offset = 8;
  let inserted = false;
  while (offset < bytes.length) {
    const length = new DataView(bytes.buffer, bytes.byteOffset + offset, 4).getUint32(0);
    const end = offset + length + 12;
    const type = new TextDecoder().decode(bytes.subarray(offset + 4, offset + 8));
    if (type !== "pHYs") chunks.push(bytes.slice(offset, end));
    if (type === "IHDR") {
      chunks.push(chunk);
      inserted = true;
    }
    offset = end;
  }
  if (!inserted) throw new Error("PNG inválido: falta cabecera IHDR");
  const parts = chunks.map((part) =>
    part.buffer.slice(part.byteOffset, part.byteOffset + part.byteLength) as ArrayBuffer,
  );
  return new Blob(parts, { type: "image/png" });
}

function createPngChunk(type: string, data: Uint8Array): Uint8Array {
  const typeBytes = new TextEncoder().encode(type);
  const chunk = new Uint8Array(data.length + 12);
  const view = new DataView(chunk.buffer);
  view.setUint32(0, data.length);
  chunk.set(typeBytes, 4);
  chunk.set(data, 8);
  view.setUint32(data.length + 8, crc32(chunk.subarray(4, data.length + 8)));
  return chunk;
}

function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
