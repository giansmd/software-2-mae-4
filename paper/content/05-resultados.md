# Resultados

## Comprensión de los datos

El dataset híbrido comprende 2 000 registros y nueve variables tras la codificación del escenario de ascenso del mar. El análisis de calidad no identificó valores faltantes ni registros duplicados en ninguna variable. La variable objetivo —variación porcentual del carbono retenido a 2050— presentó un rango de 30,27 % a −37,56 %, con una media cercana a cero, reflejo del equilibrio entre escenarios de ganancia por restauración y pérdida por ascenso del mar.

La Tabla descriptiva documenta asimetría prácticamente nula en las variables de restauración y horizonte temporal, y una dispersión reducida en el NDVI (desviación estándar de 0,023), consistente con su restricción al rango observado del manglar de franja media del SNLMT:

[[TABLA:tab04_eda_descriptivo.csv|Estadística descriptiva de las variables del dataset híbrido (n = 2 000).]]

[[FIG:fig02_distribuciones.png|Distribución de las variables principales del dataset híbrido.]]

El análisis de correlación reveló una asociación positiva moderada entre el nivel de restauración y la variación de carbono, y una asociación negativa con el escenario de ascenso del nivel del mar, coherente con la formulación del motor. Las variables de área y densidad de línea base mostraron correlación próxima a cero con la variación porcentual, lo que anticipa su escasa contribución predictiva:

[[FIG:fig03_correlacion.png|Matriz de correlación de Pearson entre las variables del estudio.]]

## Comparación de modelos

La Tabla comparativa sintetiza el desempeño de los cinco algoritmos evaluados, con las métricas del conjunto de prueba y los resultados de la validación cruzada:

[[TABLA:tab05_comparacion_modelos.csv|Comparación de los cinco modelos evaluados. R², MAE y RMSE sobre el conjunto de prueba, y R² medio con su desviación entre particiones de validación cruzada.]]

Los tres ensambles de árboles superaron el criterio de éxito establecido (R² ≥ 0,85), mientras que los modelos lineales quedaron en R² = 0,963. El ensamble **Extra Trees** obtuvo el mejor desempeño: R² = 1,000 en prueba, MAE = 0,014 puntos porcentuales y RMSE = 0,026, con una desviación estándar de cero entre las diez particiones de validación cruzada. *Random Forest* alcanzó valores prácticamente idénticos en R² pero con un MAE tres veces superior (0,048). *Gradient Boosting* quedó ligeramente por debajo (R² = 0,9996).

[[FIG:fig04_comparacion_modelos.png|Comparación del coeficiente de determinación en prueba y en validación cruzada para los cinco modelos evaluados.]]

La Figura de dispersión del mejor modelo muestra una alineación prácticamente perfecta con la recta identidad, sin patrones de desviación sistemática en ningún segmento del rango:

[[FIG:fig05_predicho_observado.png|Valores predichos frente a observados para el modelo Extra Trees.]]

[[FIG:fig06_residuales.png|Análisis de residuales del modelo Extra Trees.]]

## Validación estadística

La Tabla de pruebas estadísticas reporta el contraste del mejor modelo frente a cada alternativo, empleando la t de Student pareada sobre los puntajes por partición:

[[TABLA:tab06_pruebas_estadisticas.csv|Pruebas de significancia estadística del modelo Extra Trees frente a los modelos alternativos (t pareada y Wilcoxon sobre particiones de validación cruzada).]]

Todas las comparaciones resultaron estadísticamente significativas con p < 0,01. La diferencia frente a los modelos lineales alcanzó un estadístico t de 25,91, y frente a *Random Forest* y *Gradient Boosting* valores de 5,23 y 7,49 respectivamente. Es importante señalar que la prueba de Wilcoxon, al operar sobre solo diez particiones, presenta la máxima granularidad posible (p = 0,0625), limitación intrínseca del tamaño muestral de folds y no evidencia de ausencia de efecto.

El intervalo de confianza del 95 % para el error absoluto medio, obtenido por remuestreo bootstrap con 500 réplicas, se situó en [0,012; 0,016] puntos porcentuales, con una media de 0,014. La estrechez del intervalo confirma la estabilidad del desempeño.

La prueba de Shapiro-Wilk sobre los residuales resultó significativa (W = 0,768; p < 0,001), indicando que los errores no siguen una distribución normal. Este hallazgo justifica la inclusión de la prueba no paramétrica de Wilcoxon como contraste complementario y refuerza la robustez de la conclusión: pese a la no normalidad, ambas pruebas convergen en la superioridad del ensamble.

## Interpretabilidad y explicabilidad

La importancia por permutación identificó dos variables como determinantes y cuatro como irrelevantes para la predicción:

[[TABLA:tab07_importancia_variables.csv|Importancia por permutación de las variables del modelo Extra Trees (10 repeticiones).]]

[[FIG:fig07_importancia.png|Importancia por permutación de las variables del modelo Extra Trees.]]

El escenario de ascenso del nivel del mar encabezó la contribución (importancia media = 1,071), seguido del nivel de restauración hidrológica (0,839). Ambas variables exhibieron desviaciones estándar pequeñas (0,053 y 0,046), lo que indica estabilidad de la estimación. Las variables de horizonte temporal, área de línea base, densidad de carbono y NDVI presentaron importancia indistinguible de cero.

Este resultado es sustantivamente relevante y no un artefacto: en la formulación del motor, la variación porcentual depende exclusivamente del nivel de restauración y del escenario de nivel del mar, mientras que el área y la densidad de línea base determinan el carbono absoluto pero se cancelan en la razón porcentual. La coherencia entre la importancia empírica y la estructura del modelo físico constituye una validación indirecta del procedimiento de atribución.

## Contraste de la hipótesis

La Tabla de evidencia desagrega la respuesta por tramo de restauración hidrológica:

[[TABLA:tab08_evidencia_hipotesis.csv|Evidencia sobre la hipótesis del +25 % de retención por tramo de restauración hidrológica.]]

[[FIG:fig08_hipotesis.png|Variación media del carbono retenido por tramo de restauración hidrológica, contrastada con el umbral de la hipótesis.]]

Los resultados muestran una relación monótona creciente entre el nivel de restauración y la variación de carbono. En el tramo de restauración baja (0-25 %), la variación media fue de −17,64 %, con pérdida neta de carbono. En el tramo medio-bajo (25-50 %) se alcanzó prácticamente el equilibrio (−1,92 %). El tramo medio-alto (50-75 %) registró una ganancia media de 5,79 %, con un 17,06 % de los escenarios superando el umbral del +25 %. El tramo alto (75-100 %) alcanzó una ganancia media de 11,24 %, con un 34,85 % de los escenarios superando el umbral.

**La hipótesis del +25 % no se verifica de forma general**, sino condicional: únicamente el tramo de restauración más alto produce, en aproximadamente un tercio de los escenarios, incrementos que superan el umbral. La variación media del tramo alto (11,24 %) queda por debajo de ese valor, lo que indica que la superación del umbral depende de la interacción con el escenario de nivel del mar y del horizonte temporal.
