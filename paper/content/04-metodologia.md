# Metodología

## Área de estudio y fuentes de datos

El estudio se desarrolló sobre el Santuario Nacional Los Manglares de Tumbes (SNLMT), situado en el distrito de Zarumilla, departamento de Tumbes, Perú. El Santuario abarca 2 972 ha, de las cuales 1 779,8 ha corresponden a cobertura de manglar (68,06 %), 243 ha a bosque seco y el resto a cuerpos de agua y zonas salitrosas [[REF:almeyda2023]].

La **Tabla 1** consolida las siete clases de cobertura identificadas con sus rangos de NDVI derivados de imágenes Sentinel-2 y su extensión estimada.

[[TABLA:tab01_referencia_snlmt.csv|Clases de cobertura del SNLMT, rango de NDVI y extensión. Fuente: elaboración propia a partir de Dioses-Puelles et al. (2023).]]

La estructura de la comunidad vegetal se caracteriza mediante el índice de valor de importancia (IVI), que integra densidad, frecuencia y dominancia relativa. La **Tabla 2** presenta las cinco especies de mangle registradas y su IVI observado.

[[TABLA:tab03_especies_ivi.csv|Especies de mangle del SNLMT e índice de valor de importancia (IVI). Fuente: Dioses-Puelles et al. (2023).]]

La dinámica multitemporal de la extensión de manglar se documentó a partir de la serie Global Mangrove Watch versión 3.0, que provee once épocas entre 1996 y 2020 con resolución de 25 m bajo licencia CC BY 4.0 [[REF:bunting2022]]. La **Figura 1** presenta la evolución observada para el noroeste del Perú.

[[FIG:fig01_tendencia_gmw.png|Evolución de la extensión de manglar del SNLMT entre 1996 y 2020. Datos reales de Global Mangrove Watch v3.0. La tendencia positiva sostenida es consistente con el estatus de área natural protegida del Santuario.]]

## Diseño del dataset híbrido

El dataset empleado tiene naturaleza híbrida y explícita en su trazabilidad. Las **covariables son reales**: los rangos de restauración hidrológica, área de humedal, densidad de carbono y NDVI se anclan en los valores observados y publicados para el SNLMT. La **variable objetivo es simulada**: la variación porcentual del carbono retenido a 2050 se genera con el motor determinista del gemelo digital, cuyos parámetros son calibrables y sustituibles por mediciones de campo.

La separación explícita entre componente real y componente simulada responde a un criterio metodológico: permite auditar qué parte del resultado descansa en evidencia empírica y qué parte en la proyección del modelo físico. El motor implementa una curva saturante de respuesta a la restauración —coherente con la ley de rendimientos decrecientes observada en humedales restaurados [[REF:sadat2025]]— y una pérdida progresiva de área y densidad asociada a tres escenarios de ascenso del nivel del mar alineados con los rangos del IPCC [[REF:ipcc2013]].

Se generaron 2 000 registros con semilla fija para garantizar la reproducibilidad. La mitad de las observaciones se concentró en los extremos del rango de restauración —por debajo del 12 % y por encima del 88 %— dado que los ensambles de árboles presentan sesgo en los bordes del dominio de las variables [[REF:geurts2006]].

## Protocolo CRISP-DM

El sistema implementa las seis fases del estándar como módulos independientes y verificables.

### Fase 1. Comprensión del negocio

Se definieron un objetivo de negocio y un objetivo analítico explícitos, junto con criterios de éxito verificables establecidos *a priori*: coeficiente de determinación fuera de muestra superior o igual a 0,85; error absoluto medio inferior o igual a 3 puntos porcentuales; diferencia estadísticamente significativa frente al modelo lineal de referencia; y estabilidad entre particiones con desviación estándar del R² no superior a 0,05.

### Fase 2. Comprensión de los datos

El análisis exploratorio comprendió estadística descriptiva, diagnóstico de calidad —valores faltantes, duplicados y cardinalidad— y análisis de correlación de Pearson. La **Tabla 3** resume el comportamiento de cada variable del dataset.

[[TABLA:tab04_eda_descriptivo.csv|Estadística descriptiva de las variables del dataset híbrido (n = 2 000). La asimetría próxima a cero en las variables de restauración y horizonte confirma la ausencia de sesgo sistemático en el muestreo.]]

La **Figura 2** presenta la distribución de las variables principales. La concentración de observaciones en los extremos del rango de restauración responde al diseño experimental descrito; el NDVI muestra dispersión reducida por su restricción al rango observado del manglar de franja media.

[[FIG:fig02_distribuciones.png|Distribución de las variables principales del dataset híbrido. Los máximos en los extremos del rango de restauración son intencionales y previenen el sesgo de los ensambles de árboles en los bordes del dominio.]]

### Fase 3. Preparación de los datos

Se construyó la matriz de atributos con codificación ordinal del escenario de ascenso del mar y se separó la variable objetivo. El escalado estandarizado se aplicó **dentro** de cada pipeline de modelado, de modo que los parámetros de normalización se estiman exclusivamente sobre cada partición de entrenamiento y no contaminan la evaluación. Este diseño previene la fuga de información, error frecuente cuando el escalado se ejecuta sobre el conjunto completo antes de la partición.

### Fase 4. Modelado

Se compararon cinco algoritmos representativos de tres familias: un modelo lineal como referencia [[REF:hoerl1970]], una variante regularizada y tres ensambles de árboles [[REF:breiman2001]], [[REF:geurts2006]], [[REF:friedman2001]]. Todos se implementaron como pipelines de scikit-learn [[REF:pedregosa2011]], garantizando idéntico preprocesamiento y comparabilidad estricta.

### Fase 5. Evaluación

La evaluación combinó cuatro instrumentos complementarios. Primero, **validación cruzada** con diez particiones, empleando el R² medio entre particiones como criterio principal de selección por ser más robusto que una única partición de prueba. Segundo, **pruebas de significancia estadística** —t de Student pareada y Wilcoxon signed-rank sobre los puntajes por partición— para contrastar el mejor modelo frente a los restantes [[REF:demšar2006]], [[REF:wilcoxon1945]]. Tercero, **intervalos de confianza** del error absoluto medio mediante remuestreo bootstrap con 500 réplicas [[REF:efron1993]]. Cuarto, **verificación de supuestos** mediante la prueba de Shapiro-Wilk sobre los residuales [[REF:shapiro1965]], que orienta la elección entre pruebas paramétricas y no paramétricas.

La **interpretabilidad** se abordó mediante importancia por permutación, técnica model-agnóstica que cuantifica la caída del R² al desordenar aleatoriamente cada variable, con diez repeticiones para estimar su variabilidad [[REF:breiman2001]], [[REF:strobl2007]]. Esta elección permite auditar el modelo sin depender de supuestos sobre su estructura interna.

### Fase 6. Despliegue

La fase de despliegue se materializó en dos productos. El primero es un **panel interactivo** desarrollado en Streamlit que expone las seis fases, permite recalcular el pipeline con distintos hiperparámetros y presenta cada figura y tabla con su interpretación. El segundo es un conjunto de **reportes exportables** en formato CSV y PNG, más un documento Word generado de forma determinística a partir de secciones Markdown independientes.

## Control de versiones y trazabilidad

El desarrollo se gestionó sobre Git con historial lineal en la rama principal, acumulando 39 confirmaciones entre el 31 de agosto y el 29 de septiembre de 2026. La convención de mensajes siguió el formato de *commits* convencionales, con prefijos que identifican el tipo de cambio y referencias a los hallazgos de revisión de calidad atendidos. Esta práctica permitió reconstruir el origen de cada decisión de diseño y sostener un proceso de revisión continua sobre el código.

La gestión de incidencias se planificó sobre una plataforma de seguimiento de proyectos con tablero de tareas, historias de usuario y criterios de aceptación por incremento. Su implementación completa quedó fuera del alcance temporal del presente entregable, pero la estructura de los mensajes de confirmación preserva la relación entre cada cambio y el hallazgo o requisito que lo motivó.

## Reproducibilidad

El código se organiza en módulos con responsabilidad única: generación del dataset híbrido, motor CRISP-DM, aplicación interactiva y ensamblador de documentos. Todas las cifras del artículo se derivan automáticamente del motor; ninguna se transcribe manualmente. La semilla aleatoria es fija (42) y las versiones de las dependencias están ancladas en el archivo de requisitos, de modo que la ejecución repetida reproduce exactamente los resultados reportados.
