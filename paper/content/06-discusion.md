# Discusión

## Desempeño del emulador

Los ensambles de árboles reprodujeron el motor determinista con una fidelidad prácticamente exacta. El modelo Extra Trees alcanzó un R² de 1,000 con un error absoluto medio de 0,014 puntos porcentuales —equivalente a una desviación del orden de una centésima de punto porcentual en la variación de carbono—. Este nivel de precisión es característico de los emuladores entrenados sobre la salida de un modelo determinista: la superficie de respuesta es suave, libre de ruido de medición y completamente observable, condiciones ideales para los métodos de partición recursiva [[REF:pradisty2025]].

Ese mismo contexto explica la brecha de rendimiento frente a los modelos lineales. La superioridad del ensamble no proviene de capturar relaciones complejas ausentes en la formulación físico-química, sino de aproximar una función saturante exponencial que la regresión lineal solo puede representar mediante aproximaciones locales. La diferencia de MAE —0,014 frente a 3,024 puntos porcentuales— cuantifica esa limitación de la forma funcional, no una diferencia de calidad predictiva sobre un fenómeno con incertidumbre irreducible.

En consecuencia, estos resultados **no deben interpretarse como evidencia de que el aprendizaje automático supera a los modelos mecanicistas en la predicción de carbono azul**. La comparación relevante en la literatura involucra observaciones de campo con ruido, donde las diferencias entre familias de modelos son sustancialmente menores y los ensambles raramente alcanzan niveles de ajuste cercanos a la unidad [[REF:pradisty2025]], [[REF:zamboni2025]]. El valor del emulador es instrumental: hace tratable la exploración exhaustiva del espacio de escenarios y habilita interfaces interactivas, no reemplaza al modelo físico.

## Interpretabilidad y coherencia física

El hallazgo más informativo del análisis de explicabilidad no fue qué variables resultaron importantes, sino que la atribución coincidió exactamente con la estructura algebraica del motor. El escenario de ascenso del nivel del mar y el nivel de restauración dominan la predicción; las variables de línea base se anulan en la razón porcentual.

Esta coincidencia cumple dos funciones. Primero, valida el procedimiento de importancia por permutación como instrumento de auditoría: si hubiera asignado relevancia espuria a variables sin efecto algebraico, habría revelado un problema en el estimador o en la partición de datos. Segundo, ilustra un principio de interpretabilidad frecuentemente desatendido: **la distinción entre variables relevantes para el estado absoluto del sistema y variables relevantes para su cambio relativo**. El área y la densidad de carbono determinan el stock total —información decisiva para la valorización económica del ecosistema— pero son irrelevantes para la variación porcentual que aquí se modela.

Esta distinción tiene consecuencias prácticas directas para la gestión. Un administrador del Santuario que consulte únicamente la variación porcentual no obtendrá información sobre el carbono absoluto en riesgo, y viceversa. El panel desarrollado expone ambas dimensiones de manera explícita precisamente para evitar esa lectura parcial. La advertencia es igualmente pertinente en sentido inverso: la técnica de permutación puede forzar extrapolaciones fuera del soporte observado [[REF:hooker2019]], por lo que la coincidencia con la estructura del modelo debe leerse como consistencia interna y no como validación causal [[REF:molnar2022]].

## Implicaciones para la hipótesis de restauración

El contraste de la hipótesis arrojó un resultado más matizado que el postulado inicial. La afirmación de que la restauración hidrológica puede incrementar la retención de carbono en al menos un 25 % a 2050 **no se sostiene de forma general**, sino que se verifica condicionalmente en el tramo de intervención más alto y con una probabilidad aproximada de un tercio.

Este resultado admite dos lecturas complementarias. La primera es metodológica: el umbral del +25 % es una aspiración de política, no una propiedad del sistema físico, y el modelo revela que su consecución exige niveles de intervención cercanos a la saturación combinados con escenarios favorables de ascenso del mar. La segunda es operativa: los tramos de restauración intermedios, lejos de ser inefectivos, producen el tránsito de la pérdida neta a la ganancia neta —de −17,64 % a −1,92 %—, lo que representa un beneficio sustancial aunque no alcance el umbral aspiracional.

La relación monótona observada entre nivel de restauración y retención es consistente con la evidencia sintetizada en revisiones recientes sobre restauración de humedales costeros [[REF:sadat2025]], así como con la caracterización de respuestas no lineales dependientes de la posición topográfica y la salinidad [[REF:zamboni2025]]. La dependencia del escenario de ascenso del mar reproduce el patrón documentado de pérdida de área y densidad bajo condiciones de inundación sostenida [[REF:ipcc2013]], [[REF:lovelock2015]].

## Trazabilidad y proceso de desarrollo

La disciplina de control de versiones sostuvo la calidad del artefacto de manera verificable. Las 39 confirmaciones registradas entre agosto y septiembre de 2026 documentan no solo la incorporación de funcionalidad, sino el ciclo completo de revisión: cada hallazgo de calidad detectado quedó asociado a una confirmación que registra su corrección, con mensajes que identifican el tipo de cambio y su motivación.

Este registro cumple una función epistémica en la investigación reproducible: permite reconstruir el orden en que se tomaron las decisiones de diseño y auditar el estado exacto del sistema sobre el que se ejecutaron los análisis reportados. La planificación de incidencias sobre plataforma de seguimiento se proyectó como complemento, pero su implementación completa excedió el alcance temporal del entregable; la estructura de los mensajes preserva la relación entre cada cambio y el hallazgo que lo originó, de modo que la trazabilidad no se perdió con esa omisión.

## Limitaciones

El presente trabajo presenta cuatro limitaciones que deben considerarse al interpretar sus resultados.

La primera y más importante es que **la variable objetivo es simulada**. Aunque las covariables provienen de datos reales publicados y la estructura del motor es coherente con la literatura, los resultados describen el comportamiento del modelo, no del ecosistema. Las métricas de desempeño cuantifican la fidelidad del emulador respecto del motor, no la capacidad predictiva sobre observaciones de campo. La sustitución de los parámetros calibrados por mediciones del SNLMT es el paso necesario para que las proyecciones adquieran validez empírica.

La segunda es la **ausencia de estructura espacial**. El modelo opera sobre valores agregados a escala de sitio, sin representar la heterogeneidad topográfica, la conectividad hidrológica entre franjas de manglar ni los gradientes de salinidad que la literatura identifica como determinantes de la respuesta a la restauración [[REF:zamboni2025]].

La tercera es la **representación simplificada de la dinámica temporal**. La formulación emplea una progresión lineal entre el año inicial y el horizonte, mientras que las trayectorias reales de acreción y acumulación de carbono siguen patrones asintóticos y presentan dependencia de la historia de intervención previa [[REF:woodroffe2016]].

La cuarta es la **granularidad del contraste estadístico**. Con diez particiones de validación cruzada, la prueba de Wilcoxon alcanza su mínimo valor de probabilidad posible (p = 0,0625) sin poder cruzar el umbral de 0,05. Esta limitación es intrínseca al diseño y no a la magnitud del efecto; la t pareada, que aprovecha la magnitud de las diferencias y no solo su signo, sí alcanza significancia con p < 0,001 en todas las comparaciones.

## Trabajo futuro

Tres líneas de continuidad se desprenden directamente de estas limitaciones. La incorporación de mediciones de campo del SNLMT —parcelas de monitoreo permanente y perfiles de carbono orgánico del suelo— permitiría recalibrar el motor y validar las proyecciones contra observaciones independientes. La integración de capas ráster de cobertura y elevación habilitaría la representación de la heterogeneidad espacial y la exploración de escenarios de restauración diferenciados por franja. Finalmente, la incorporación de modelos de acumulación que representen explícitamente la saturación temporal mejoraría la fidelidad de las proyecciones de largo plazo.

Desde la perspectiva del despliegue, la arquitectura del panel admite la incorporación de nuevos módulos analíticos sin modificar los existentes, de modo que cada una de estas líneas puede integrarse de manera incremental conservando la trazabilidad entre objetivos de gestión y artefactos analíticos que estructura la metodología CRISP-DM.
