# Resumen

Los gemelos digitales de ecosistemas naturales constituyen un paradigma emergente para el monitoreo y la gestión ambiental, aunque su aplicación a humedales costeros del Pacífico suroriental permanece escasamente documentada. Este estudio presenta un **gemelo digital** del Santuario Nacional Los Manglares de Tumbes (SNLMT), en el norte del Perú, aplicando la metodología **CRISP-DM** para modelar y explicar la variación del carbono retenido bajo escenarios de restauración hidrológica y ascenso del nivel del mar hasta 2050.

El dataset es de naturaleza **híbrida**: las covariables y la calibración provienen de datos reales publicados sobre el SNLMT —extensión y cobertura por clase, rangos de índice de vegetación de diferencia normalizada (NDVI), índice de valor de importancia (IVI) por especie y contenido de carbono azul—, mientras que la variable objetivo se genera con un motor determinista parametrizable, replicable y sustituible por mediciones de campo. La separación explícita entre ambas porciones responde a la exigencia de transparencia que la literatura sobre gemelos digitales ecológicos formula de manera consistente.

Se evaluaron cinco algoritmos de aprendizaje supervisado mediante validación cruzada de diez particiones, pruebas de significancia estadística (t pareada y Wilcoxon), intervalos de confianza por remuestreo bootstrap e interpretabilidad mediante importancia por permutación. El ensamble **Extra Trees** alcanzó el mejor desempeño (R² = 1,000; MAE = 0,014 puntos porcentuales), significativamente superior a la línea base lineal (t = 25,91; p < 0,001). La restauración hidrológica produjo incrementos superiores al umbral del +25 % en un 34,85 % de los escenarios del tramo de intervención alta, con una ganancia media de 11,24 %, mientras que los tramos intermedios produjeron el tránsito de la pérdida neta a la ganancia neta.

Los resultados se materializan en un panel interactivo y en reportes exportables que documentan cada fase analítica, con trazabilidad de control de versiones sobre 39 confirmaciones de código.

**Palabras clave:** gemelo digital; humedal costero; carbono azul; restauración hidrológica; CRISP-DM; Tumbes; Perú.
