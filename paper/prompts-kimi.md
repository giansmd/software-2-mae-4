# Prompts para Kimi — MAE-4

Generados el 2026-09-29. Ejecutar en Kimi adjuntando `GD.docx`.

---

## PROMPT 1 — Mejora del prompt de artículo científico

Copia todo el bloque de abajo en Kimi.

```
Actúa como metodólogo experto en publicación científica y en ingeniería de
prompts. Tu tarea es MEJORAR el siguiente prompt, no ejecutarlo todavía.

=== PROMPT ORIGINAL A MEJORAR ===
"Haz el papel de un experto escritor de artículos científicos para revistas de
nivel Q1. Tu misión es elaborar un artículo de investigación titulado [Título]
en base al análisis exhaustivo del código adjunto [GD.docx], debe contener 6
gráficos y 6 tablas relevantes, simula resultados con datos que puedan ser
después reemplazados con datos reales, debe contener por lo menos 40
referencias en formato APA. El artículo científico debe satisfacer las
exigencias de fondo y de forma de una revista de nivel Q1"
=== FIN DEL PROMPT ORIGINAL ===

CONTEXTO QUE DEBES INCORPORAR:
- El artefacto adjunto (GD.docx) NO es solo código: contiene el código y la
  documentación técnica de un gemelo digital de carbono azul para el manglar
  del Santuario Nacional Los Manglares de Tumbes (Perú).
- El proyecto ya cuenta con: dataset híbrido (datos reales publicados +
  proyección simulada), motor analítico con las seis fases CRISP-DM, panel
  interactivo en Streamlit con interpretabilidad (importancia por permutación),
  validación cruzada, pruebas estadísticas (t pareada, Wilcoxon, bootstrap,
  Shapiro-Wilk) y resultados numéricos reales.
- La revista objetivo es "Manglar" (Universidad Nacional de Tumbes, Perú):
  acceso abierto, sin costo de publicación, publica en español e inglés,
  artículos originales y de revisión, alcance en biodiversidad y servicios
  ecosistémicos, uso sostenible de bosques y ciencia ambiental.

REQUISITOS DE LA MEJORA:
1. Corrige las deficiencias del prompt original: ambigüedad de [Título],
   instrucción contradictoria entre "simula resultados" y "datos reales",
   número fijo de figuras/tablas impuesto sin justificación, y ausencia de
   criterios de verificabilidad.
2. Especifica de forma accionable: estructura seccional, extensión por
   sección, voz narrativa, tratamiento del rigor estadístico y cómo declarar
   la naturaleza híbrida del dataset sin comprometer la honestidad científica.
3. Incorpora el requisito de que TODA figura y tabla lleve interpretación
   explícita y que la discusión distinga entre hallazgos del modelo físico y
   capacidad predictiva del emulador.
4. Añade criterios de auto-verificación que el modelo pueda comprobar antes de
   entregar (coherencia numérica con las tablas, citas efectivamente usadas,
   ausencia de afirmaciones no sustentadas).
5. Entrega el prompt mejorado como un bloque único listo para copiar, seguido
   de una lista breve de los cambios que hiciste y por qué.

Devuelve ÚNICAMENTE: (a) el prompt mejorado en un bloque de código, y (b) la
justificación de cambios. No redactes el artículo todavía.
```

---

## PROMPT 2 — Mejora del prompt de recomendación de revistas

Copia todo el bloque de abajo en Kimi.

```
Actúa como metodólogo experto en publicación científica y en ingeniería de
prompts. Tu tarea es MEJORAR el siguiente prompt, no ejecutarlo todavía.

=== PROMPT ORIGINAL A MEJORAR ===
"Haz el papel de un experto escritor de artículos científicos de alto impacto
de nivel Q1. Para el artículo científico adjunto [GD.docx] recomienda revistas
de nivel Q2, Q3 y Scopus y/o Web of Science de acceso abierto y gratuitas, a
las cuales se puede enviar el artículo de investigación para su aceptación y
publicación."
=== FIN DEL PROMPT ORIGINAL ===

CONTEXTO Y RESTRICCIONES REALES (críticas para la mejora):
- El requisito efectivo del trabajo es una revista **Q3, indexada en Scopus y
  SIN costo de publicación (sin APC)**.
- Ya se verificó que la intersección "Q3 + Scopus + sin APC" es muy estrecha
  en ciencias ambientales. La mejora debe exigir al modelo EXPLICITAR la
  verificación de cada candidata en fuentes primarias (Scimago, DOAJ, sitio
  oficial de la revista) y no aceptar listados agregadores de terceros sin
  comprobación, porque estos frecuentemente reportan mal el APC.
- Cuando una revista no cumpla todos los criterios, el modelo debe decirlo
  explícitamente en lugar de forzar el encaje.

REQUISITOS DE LA MEJORA:
1. Exige que toda recomendación incluya, como mínimo: nombre exacto, ISSN,
   editorial, cuartil Scimago con la categoría temática y el año, índice de
   impacto o SJR, política de APC verificada en el sitio oficial, licencia,
   idiomas aceptados, tiempo declarado de revisión y enlace a las
   instrucciones para autores.
2. Exige declarar el "mejor cuartil" además del cuartil vigente, para evitar
   presentar como Q3 una revista que hoy es Q4 o Q2.
3. Exige una tabla comparativa y una recomendación jerarquizada con
   justificación, más una sección explícita de revistas DESCARTADAS y el
   motivo del descarte.
4. Añade la obligación de distinguir entre revistas verificadas en fuente
   primaria y revistas solo referenciadas desde agregadores.
5. Entrega el prompt mejorado como un bloque único listo para copiar, seguido
   de la justificación de cambios.

Devuelve ÚNICAMENTE: (a) el prompt mejorado en un bloque de código, y (b) la
justificación de cambios. No ejecutes la búsqueda todavía.
```

---

## PROMPT 3 — Adecuación al formato de Manglar

Úsalo después de tener el artículo y la revista confirmada.

```
Actúa como editor científico especializado en adecuación de manuscritos a
normas editoriales de revistas indexadas.

CONTEXTO: el manuscrito adjunto está destinado a la revista "Manglar"
(Universidad Nacional de Tumbes, Perú; e-ISSN 2414-1046). Es una revista de
acceso abierto, sin costo de publicación, que publica artículos originales y de
revisión en español e inglés.

TAREA: adecúa el manuscrito a las exigencias de fondo y de forma de la
revista, conservando íntegramente el contenido científico.

Aspectos de FORMA a verificar y corregir:
- Estructura seccional exigida por la revista.
- Formato de título, autores, filiaciones y autor de correspondencia.
- Formato de resumen y palabras clave (cantidad y idioma).
- Sistema de citación y lista de referencias: la revista usa orden alfabético
  y estilo APA; verifica consistencia total entre citas en texto y referencias.
- Numeración y pies de figuras y tablas, con llamada explícita en el texto.
- Unidades del Sistema Internacional y notación decimal.
- Los agregados de terceros no indexados (tesis, páginas web) deben ser
  mínimos y justificados.

Aspectos de FONDO a verificar:
- Correspondencia entre objetivos, método, resultados y conclusiones.
- Declaración explícita de la naturaleza de los datos (reales vs. simulados).
- Justificación estadística de cada afirmación cuantitativa.
- Sección de limitaciones que no contradiga las conclusiones.

ENTREGA: el manuscrito completo adecuado, más una lista de verificación de
cambios. Marca explícitamente cualquier punto donde el manuscrito NO cumpla un
requisito de la revista, en lugar de corregirlo silenciosamente.
```
