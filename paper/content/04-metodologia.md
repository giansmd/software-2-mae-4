# Metodología

## Área de estudio y fuentes de datos

El estudio se desarrolló sobre el Santuario Nacional Los Manglares de Tumbes (SNLMT), situado en el distrito de Zarumilla, departamento de Tumbes, Perú. El Santuario abarca 2 972 ha, de las cuales 1 779,8 ha corresponden a cobertura de manglar (68,06 %), 243 ha a bosque seco y el resto a cuerpos de agua y zonas salitrosas [[REF:almeyda2023]].

La Tabla de referencia consolida las siete clases de cobertura identificadas con sus rangos de NDVI derivados de imágenes Sentinel-2 y su extensión:

[[TABLA:tab01_referencia_snlmt.csv|Clases de cobertura del SNLMT, rango de NDVI y extensión. Fuente: elaboración propia a partir de Dioses-Puelles et al. (2023).]]

La estructura de la comunidad vegetal se caracteriza mediante el índice de valor de importancia (IVI), que integra densidad, frecuencia y dominancia relativa:

[[TABLA:tab03_especies_ivi.csv|Especies de mangle del SNLMT y su índice de valor de importancia (IVI). Fuente: Dioses-Puelles et al. (2023).]]

La dinámica multitemporal de la extensión de manglar se documentó a partir de la serie Global Mangrove Watch versión 3.0, que provee once épocas entre 1996 y 2020 con resolución de 25 m bajo licencia CC BY 4.0 [[REF:bunting2022]]:

[[TABLA:tab02_gmw_serie.csv|Serie multitemporal de extensión de manglar del noroeste del Perú. Fuente: Global Mangrove Watch v3.0 (CC BY 4.0).]]

[[FIG:fig01_tendencia_gmw.png|Evolución de la extensión de manglar del SNLMT entre 1996 y 2020. Datos reales de Global Mangrove Watch v3.0.]]

## Diseño del dataset híbrido

El dataset empleado tiene naturaleza híbrida y explícita en su trazabilidad. Las **covariables son reales**: los rangos de restauración hidrológica, área de humedal, densidad de carbono y NDVI se anclan en los valores observados y publicados para el SNLMT. La **variable objetivo es simulada**: la variación porcentual del carbono retenido a 2050 se genera con el motor determinista del gemelo digital, cuyos parámetros son calibrables y sustituibles por mediciones de campo.

La separación explícita entre componente real y componente simulada responde a un criterio metodológico: permite auditar qué parte del resultado descansa en evidencia empírica y qué parte en la proyección del modelo físico. El motor implementa una curva saturante de respuesta a la restauración —coherente con la ley de rendimientos decrecientes observada en humedales restaurados [[REF:sadat2025]]— y una pérdida progresiva de área y densidad asociada a tres escenarios de ascenso del nivel del mar alineados con los rangos del IPCC [[REF:ipcc2013]].

Se generaron 2 000 registros con semilla fija para garantizar la reproducibilidad. La mitad de las observaciones se concentró en los extremos del rango de restauración —por debajo del 12 % y por encima del 88 %— dado que los ensambles de árboles presentan sesgo en los bordes del dominio de las variables.

## Protocolo CRISP-DM

### Fase 1. Comprensión del negocio

Se definieron un objetivo de negocio y un objetivo analítico explícitos, junto con criterios de éxito verificables establecidos *a priori*: coeficiente de determinación fuera de muestra superior o igual a 0,85; error absoluto medio inferior o igual a 3 puntos porcentuales; diferencia estadísticamente significativa frente al modelo lineal de referencia; y estabilidad entre particiones con desviación estándar del R² no superior a 0,05.

### Fase 2. Comprensión de los datos

El análisis exploratorio comprendió estadística descriptiva, diagnóstico de calidad —valores faltantes, duplicados y cardinalidad—, y análisis de correlación de Pearson entre variables numéricas. La Tabla descriptiva resume el comportamiento de cada variable:

[[TABLA:tab04_eda_descriptivo.csv|Estadística descriptiva de las variables del dataset híbrido (n = 2 000).]]

[[FIG:fig02_distribuciones.png|Distribución de las variables principales del dataset híbrido.]]

[[FIG:fig03_correlacion.png|Matriz de correlación de Pearson entre las variables del estudio.]]

### Fase 3. Preparación de los datos

Se construyó la matriz de atributos con codificación ordinal del escenario de ascenso del mar y se separó la variable objetivo. El escalado estandarizado se aplicó **dentro** de cada pipeline de modelado, de modo que los parámetros de normalización se estiman exclusivamente sobre cada partición de entrenamiento y no contaminan la evaluación. Este diseño previene la fuga de información, error frecuente cuando el escalado se ejecuta sobre el conjunto completo antes de la partición.

### Fase 4. Modelado

Se compararon cinco algoritmos representativos de tres familias: un modelo lineal como referencia (*Regresión lineal*), una variante regularizada (*Ridge*) y tres ensambles de árboles (*Random Forest*, *Extra Trees* y *Gradient Boosting*). Todos se implementaron como pipelines de scikit-learn [[REF:pedregosa2011]], garantizando idéntico preprocesamiento y comparabilidad estricta.

### Fase 5. Evaluación

La evaluación combinó cuatro instrumentos complementarios. Primero, **validación cruzada** con diez particiones sobre el conjunto de entrenamiento, empleando el R² medio entre particiones como criterio principal de selección por ser más robusto que una única partición de prueba. Segundo, **pruebas de significancia estadística** —t de Student pareada y Wilcoxon signed-rank sobre los puntajes por partición— para contrastar el mejor modelo frente a los restantes [[REF:demšar2006]]. Tercero, **intervalos de confianza** del error absoluto medio mediante remuestreo bootstrap con 500 réplicas. Cuarto, **verificación de supuestos** mediante la prueba de Shapiro-Wilk sobre los residuales, que orienta la elección entre pruebas paramétricas y no paramétricas.

La **interpretabilidad** se abordó mediante importancia por permutación, técnica model-agnóstica que cuantifica la caída del R² al desordenar aleatoriamente cada variable, con diez repeticiones para estimar su variabilidad [[REF:breiman2001]]. Esta elección permite auditar el modelo sin depender de supuestos sobre su estructura interna.

### Fase 6. Despliegue

La fase de despliegue se materializó en dos productos. El primero es un **panel interactivo** desarrollado en Streamlit que expone las seis fases, permite recalcular el pipeline con distintos hiperparámetros y presenta cada figura y tabla con su interpretación. El segundo es un conjunto de **reportes exportables** en formato CSV y PNG, más un documento Word generado de forma determinística a partir de secciones Markdown independientes.

## Reproducibilidad

El código se organiza en módulos con responsabilidad única: generación del dataset híbrido, motor CRISP-DM, aplicación interactiva y ensamblador de documentos. Todas las cifras del artículo se derivan automáticamente del motor; ninguna se transcribe manualmente. La semilla aleatoria es fija (42) y las versiones de las dependencias están ancladas en el archivo de requisitos, de modo que la ejecución repetida reproduce exactamente los resultados reportados.
