# Marco teórico

## Carbono azul en ecosistemas de manglar

El término *carbono azul* designa el carbono orgánico capturado y almacenado por ecosistemas marinos y costeros vegetados [[REF:mcleod2011]]. En los manglares, la mayor fracción del carbono se acumula en el sedimento más que en la biomasa aérea: estudios globales sitúan entre el 50 % y el 90 % del total en los primeros metros de suelo [[REF:donato2011]]. Esta distribución vertical explica por qué la pérdida de cobertura no solo reduce la captura anual, sino que libera stocks acumulados durante siglos, con emisiones que pueden superar las 1 000 Mg CO₂e por hectárea convertida [[REF:kauffman2017]].

Las estimaciones globales sugieren que la pérdida de manglares contribuye de manera desproporcionada al balance de carbono atmosférico respecto de su superficie total, lo que ha impulsado su incorporación en los inventarios nacionales y en los mercados voluntarios de carbono [[REF:nature2026]]. El SNLMT ha iniciado ese tránsito mediante un proceso de certificación bajo el estándar Plan Vivo [[REF:consorcio2023]].

## Restauración hidrológica

La restauración hidrológica busca restablecer los regímenes de inundación y salinidad que sostienen la productividad del manglar. La evidencia sintetizada en revisiones recientes indica que la recuperación de la conectividad tidal incrementa la acreción sedimentaria, eleva las tasas de acumulación de carbono orgánico y mejora la estabilidad estructural del ecosistema [[REF:sadat2025]]. No obstante, la magnitud del efecto depende de la posición topográfica, la salinidad intersticial y la disponibilidad de propágulos, de modo que la respuesta no es lineal ni uniforme [[REF:zamboni2025]].

La modelización del efecto de la restauración exige, por tanto, representar explícitamente la saturación de la respuesta: a mayor nivel de intervención, menor ganancia marginal. Esta consideración motiva la forma funcional saturante empleada en el motor de simulación descrito en la metodología.

## Aprendizaje automático como emulador y como instrumento explicativo

Los emuladores —*surrogates*— son modelos estadísticos entrenados para reproducir la salida de un modelo físico a una fracción del costo computacional [[REF:pradisty2025]]. En el contexto de los humedales costeros permiten explorar de manera exhaustiva el espacio de escenarios, sostener análisis de sensibilidad y alimentar interfaces interactivas.

Los ensambles de árboles —Random Forest y Extra Trees— son especialmente adecuados para esta tarea: capturan interacciones no lineales, son robustos frente a escalas heterogéneas de las variables y proveen medidas de importancia directamente interpretables [[REF:breiman2001]]. Su adopción en teledetección de manglares está ampliamente documentada [[REF:pradisty2025]].

La contrapartida de su capacidad predictiva es la opacidad. La importancia por permutación y los métodos de atribución local resuelven parcialmente este problema al cuantificar la contribución de cada variable a la predicción, y constituyen hoy un requisito práctico para la adopción de modelos en la gestión ambiental [[REF:mcNulty2025]].

## Metodología CRISP-DM

CRISP-DM —*Cross-Industry Standard Process for Data Mining*— organiza un proyecto analítico en seis fases iterativas: comprensión del negocio, comprensión de los datos, preparación de los datos, modelado, evaluación y despliegue [[REF:wirth2000]]. A diferencia de aproximaciones centradas exclusivamente en el algoritmo, el estándar exige que cada artefacto analítico sea trazable hasta un objetivo de negocio explícito, y que la evaluación contemple criterios de éxito definidos *a priori*.

En aplicaciones ambientales, CRISP-DM facilita la comunicación entre equipos técnicos y gestores, y reduce el riesgo de producir modelos estadísticamente sólidos pero irrelevantes para la decisión [[REF:sadat2025]]. El presente trabajo adopta este marco y documenta cada fase con sus productos verificables.
