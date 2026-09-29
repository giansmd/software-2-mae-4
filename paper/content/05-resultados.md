# Resultados

## Comparación de modelos

La **Tabla 4** sintetiza el desempeño de los cinco algoritmos evaluados, con las métricas del conjunto de prueba y los resultados de la validación cruzada de diez particiones.

[[TABLA:tab05_comparacion_modelos.csv|Comparación de los cinco modelos evaluados. R², MAE y RMSE sobre el conjunto de prueba, y R² medio con su desviación entre particiones de validación cruzada. Los tres ensambles superan el criterio de éxito de R² ≥ 0,85.]]

Los tres ensambles de árboles superaron el criterio de éxito establecido (R² ≥ 0,85), mientras que los modelos lineales quedaron en R² = 0,963. El ensamble **Extra Trees** obtuvo el mejor desempeño: R² = 1,000 en prueba, MAE = 0,014 puntos porcentuales y RMSE = 0,026, con una desviación estándar de cero entre las diez particiones de validación cruzada. *Random Forest* alcanzó valores idénticos en R² pero con un MAE más de tres veces superior (0,048). *Gradient Boosting* quedó ligeramente por debajo (R² = 0,9996).

La **Figura 3** compara visualmente el coeficiente de determinación en prueba y en validación cruzada. La equivalencia entre ambas métricas para cada modelo descarta sobreajuste: el desempeño se mantiene estable fuera de la partición de entrenamiento.

[[FIG:fig04_comparacion_modelos.png|Comparación del coeficiente de determinación en prueba y en validación cruzada para los cinco modelos evaluados. La proximidad entre ambas barras en cada modelo indica ausencia de sobreajuste.]]

La **Figura 4** presenta la dispersión de valores predichos frente a observados para el modelo seleccionado, con alineación prácticamente perfecta respecto de la recta identidad y sin patrones de desviación sistemática en ningún segmento del rango.

[[FIG:fig05_predicho_observado.png|Valores predichos frente a observados para el modelo Extra Trees. La ausencia de curvatura o heterocedasticidad indica que el ensamble reproduce la superficie de respuesta del motor sin sesgo direccional.]]

## Validación estadística

La **Tabla 5** reporta el contraste del mejor modelo frente a cada alternativa, empleando la t de Student pareada sobre los puntajes por partición.

[[TABLA:tab06_pruebas_estadisticas.csv|Pruebas de significancia estadística del modelo Extra Trees frente a los modelos alternativos (t pareada y Wilcoxon sobre particiones de validación cruzada).]]

Todas las comparaciones resultaron estadísticamente significativas con p < 0,01. La diferencia frente a los modelos lineales alcanzó un estadístico t de 25,91, y frente a *Random Forest* y *Gradient Boosting* valores de 5,23 y 7,49 respectivamente. Es importante señalar que la prueba de Wilcoxon, al operar sobre solo diez particiones, presenta la máxima granularidad posible (p = 0,0625), limitación intrínseca del tamaño muestral de particiones y no evidencia de ausencia de efecto.

El intervalo de confianza del 95 % para el error absoluto medio, obtenido por remuestreo bootstrap con 500 réplicas, se situó en [0,012; 0,016] puntos porcentuales, con una media de 0,014. La estrechez del intervalo confirma la estabilidad del desempeño entre remuestreos.

La prueba de Shapiro-Wilk sobre los residuales resultó significativa (W = 0,768; p < 0,001), indicando que los errores no siguen una distribución normal. Este hallazgo justifica la inclusión de la prueba no paramétrica de Wilcoxon como contraste complementario y refuerza la robustez de la conclusión: pese a la no normalidad, ambas pruebas convergen en la superioridad del ensamble.

La magnitud de esa no normalidad merece precisión. Dado que los residuales presentan una distribución de colas marcadamente concentradas —con la mayoría de los errores próximos a cero—, la desviación respecto de la normalidad refleja una precisión superior a la que el supuesto paramétrico anticiparía, no un defecto del modelo. Este patrón es característico de los emuladores sobre modelos deterministas, donde la superficie de respuesta carece del ruido aleatorio que habitualmente produce residuales gaussianos.

## Interpretabilidad y explicabilidad

La **Tabla 6** presenta la importancia por permutación de cada variable, con su variabilidad sobre diez repeticiones.

[[TABLA:tab07_importancia_variables.csv|Importancia por permutación de las variables del modelo Extra Trees (10 repeticiones). La desviación estándar reducida en las variables relevantes confirma la estabilidad de la estimación.]]

La **Figura 5** representa gráficamente esa jerarquía de contribuciones, con barras de error correspondientes a las diez repeticiones.

[[FIG:fig07_importancia.png|Importancia por permutación de las variables del modelo Extra Trees, con barras de error correspondientes a diez repeticiones.]]

El escenario de ascenso del nivel del mar encabezó la contribución (importancia media = 1,071), seguido del nivel de restauración hidrológica (0,839). Ambas variables exhibieron desviaciones estándar pequeñas (0,053 y 0,046), lo que indica estabilidad de la estimación. Las variables de horizonte temporal, área de línea base, densidad de carbono y NDVI presentaron importancia indistinguible de cero.

Este resultado es sustantivamente relevante y no un artefacto. En la formulación del motor, la variación porcentual depende exclusivamente del nivel de restauración y del escenario de nivel del mar, mientras que el área y la densidad de línea base determinan el carbono absoluto pero se cancelan en la razón porcentual. La coherencia entre la importancia empírica y la estructura del modelo físico constituye una validación indirecta del procedimiento de atribución.

La distinción no es meramente técnica. Las variables descartadas —área y densidad de línea base— son precisamente las que determinan el carbono absoluto en riesgo, información crítica para la valorización económica del ecosistema. Un modelo optimizado únicamente para predecir la variación porcentual resulta ciego a esa dimensión, lo que refuerza la necesidad de exponer ambas métricas de manera conjunta en cualquier instrumento de apoyo a la decisión.

## Contraste de la hipótesis

La **Figura 6** desagrega la respuesta por tramo de restauración hidrológica, contrastándola con el umbral del +25 % postulado en la hipótesis.

[[FIG:fig08_hipotesis.png|Variación media del carbono retenido por tramo de restauración hidrológica, contrastada con el umbral de la hipótesis del +25 %. La relación monótona creciente indica rendimientos decrecientes pero sostenidos.]]

Los resultados muestran una relación monótona creciente entre el nivel de restauración y la variación de carbono. En el tramo de restauración baja (0-25 %), la variación media fue de −17,64 %, con pérdida neta de carbono. En el tramo medio-bajo (25-50 %) se alcanzó prácticamente el equilibrio (−1,92 %). El tramo medio-alto (50-75 %) registró una ganancia media de 5,79 %, con un 17,06 % de los escenarios superando el umbral. El tramo alto (75-100 %) alcanzó una ganancia media de 11,24 %, con un 34,85 % de los escenarios superando el umbral del +25 %.

**La hipótesis del +25 % no se verifica de forma general**, sino condicional: únicamente el tramo de restauración más alto produce, en aproximadamente un tercio de los escenarios, incrementos que superan el umbral. La variación media de ese tramo (11,24 %) queda por debajo del valor postulado, lo que indica que la superación depende de la interacción con el escenario de nivel del mar y del horizonte temporal.
