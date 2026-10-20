// Exporta gráficos SVG (Recharts) a PNG 600 DPI y SVG vectorial.
// Los metadatos de interpretabilidad (título, ejes, leyenda, fuente) ya
// viven dentro del SVG renderizado por Recharts. Esta utilidad solo
// rasteriza a alta resolución para publicación científica.

const DPI_TARGET = 600;
const DPI_SCREEN = 96;
const SCALE = DPI_TARGET / DPI_SCREEN; // ≈ 6.25

/**
 * Rasteriza el SVG encontrado en `container` a PNG 600 DPI.
 * Inyecta una nota al pie (source + date) dentro del SVG clonado
 * antes de rasterizar, para que la nota aparezca en el PNG final.
 */
export async function exportChartPng(
  container: HTMLElement,
  filename: string,
  note?: string,
): Promise<void> {
  const svg = container.querySelector("svg");
  if (!svg) throw new Error("SVG no encontrado en el contenedor");

  // Clonar para no mutar el DOM visible
  const clone = svg.cloneNode(true) as SVGElement;

  // Asegurar xmlns (algunos navegadores lo omiten al serializar)
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");

  // Dimensiones del SVG original (está en el DOM). El clon NO tiene layout.
  const bbox = svg.getBoundingClientRect();
  const w = bbox.width;
  const originalH = bbox.height;
  const h = originalH + (note ? 40 : 0);
  if (!w || !originalH) throw new Error("El gráfico aún no tiene dimensiones visibles");

  // Si hay nota, ampliar viewBox y añadir <text> al pie
  if (note) injectNote(clone, note, w, originalH);

  // Forzar width/height explícitos en el clon para que <img> los respete
  clone.setAttribute("width", String(w));
  clone.setAttribute("height", String(h));

  const svgString = new XMLSerializer().serializeToString(clone);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  await new Promise<void>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(w * SCALE);
      canvas.height = Math.round(h * SCALE);
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        URL.revokeObjectURL(url);
        reject(new Error("No se pudo crear el canvas"));
        return;
      }
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(SCALE, SCALE);
      ctx.drawImage(img, 0, 0, w, h);

      canvas.toBlob(
        (b) => {
          URL.revokeObjectURL(url);
          if (!b) {
            reject(new Error("El navegador rechazó generar el PNG"));
            return;
          }
          downloadBlob(b, `${filename}.png`);
          resolve();
        },
        "image/png",
        1.0,
      );
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("El navegador no pudo cargar el SVG (revisa consola)"));
    };
    img.src = url;
  });
}

/**
 * Exporta el SVG tal cual (vectorial) — ideal para LaTeX / Illustrator.
 */
export function exportChartSvg(container: HTMLElement, filename: string): void {
  const svg = container.querySelector("svg");
  if (!svg) throw new Error("SVG no encontrado en el contenedor");
  const clone = svg.cloneNode(true) as SVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  const str = new XMLSerializer().serializeToString(clone);
  const blob = new Blob([str], { type: "image/svg+xml;charset=utf-8" });
  downloadBlob(blob, `${filename}.svg`);
}

function injectNote(svg: SVGElement, note: string, w: number, h: number): void {
  const vb = svg.getAttribute("viewBox");
  const [vx, vy, vw, vh] = vb
    ? vb.split(/\s+/).map(Number)
    : [0, 0, w, h];

  // Ampliar viewBox 40px abajo
  svg.setAttribute("viewBox", `${vx} ${vy} ${vw} ${vh + 40}`);
  svg.setAttribute("height", String(h + 40));

  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", String(vx + 8));
  text.setAttribute("y", String(vy + vh + 24));
  text.setAttribute("font-size", "11");
  text.setAttribute("font-family", "Arial, sans-serif");
  text.setAttribute("fill", "#555555");
  text.textContent = note;
  svg.appendChild(text);
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
 * Construye la nota de interpretabilidad estándar para artículo científico.
 */
export function buildNote(parts: {
  source: string;
  method?: string;
  date?: string;
  params?: string;
}): string {
  const date = parts.date ?? new Date().toISOString().slice(0, 10);
  const segs = [`Fuente: ${parts.source}`];
  if (parts.method) segs.push(`Método: ${parts.method}`);
  if (parts.params) segs.push(parts.params);
  segs.push(`Fecha: ${date}`);
  return segs.join(" · ");
}
