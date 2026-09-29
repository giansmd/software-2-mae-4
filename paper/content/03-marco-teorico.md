# Marco teórico

## Carbono azul en ecosistemas de manglar

El término *carbono azul* designa el carbono orgánico capturado y almacenado por ecosistemas marinos y costeros vegetados [[REF:mcleod2011]]. En los manglares, la mayor fracción del carbono se acumula en el sedimento más que en la biomasa aérea: estudios globales sitúan entre el 50 % y el 90 % del total en los primeros metros de suelo [[REF:donato2011]]. Esta distribución vertical explica por qué la pérdida de cobertura no solo reduce la captura anual, sino que libera reservas acumuladas durante siglos, con emisiones que pueden superar las 1 000 Mg CO₂e por hectárea convertida [[REF:kauffman2017]].

Las estimaciones globales sugieren que la pérdida de manglares contribuye de manera desproporcionada al balance de carbono atmosférico respecto de su superficie total, lo que ha impulsado su incorporación en los inventarios nacionales y en los mercados voluntarios de carbono [[REF:macreadie2019]]. El SNLMT ha iniciado ese tránsito mediante un proceso de certificación bajo el estándar Plan Vivo [[REF:consorcio2023]].

El monitoreo de estos ecosistemas ha experimentado una transformación metodológica con la disponibilidad de series satelitales de largo plazo. La iniciativa Global Mangrove Watch estableció una línea base global de extensión de manglar y su evolución multitemporal entre 1996 y 2020, con resolución de 25 metros y licencia de uso abierto [[REF:bunting2018]], [[REF:bunting2022]]. Esta infraestructura de datos permite anclar modelos locales en observaciones verificables.

## Restauración hidrológica

La restauración hidrológica busca restablecer los regímenes de inundación y salinidad que sostienen la productividad del manglar. La evidencia sintetizada en revisiones recientes indica que la recuperación de la conectividad tidal incrementa la acreción sedimentaria, eleva las tasas de acumulación de carbono orgánico y mejora la estabilidad estructural del ecosistema [[REF:sadat2025]]. No obstante, la magnitud del efecto depende de la posición topográfica, la salinidad intersticial y la disponibilidad de propágulos, de modo que la respuesta no es lineal ni uniforme [[REF:zamboni2025]].

La vulnerabilidad del manglar frente al ascenso del nivel del mar constituye el principal factor modulador de esa respuesta. La capacidad de ajuste vertical del sustrato determina si el ecosistema mantiene su posición en la franja intermareal o si la pierde por inundación sostenida [[REF:krauss2014]], [[REF:lovelock2015]]. Los procesos de sedimentación y la respuesta relativa del nivel del mar condicionan, en última instancia, la permanencia del bosque [[REF:woodroffe2016]].

La modelización del efecto conjunto de la restauración y del ascenso del mar exige, por tanto, representar explícitamente la saturación de la respuesta: a mayor nivel de intervención, menor ganancia marginal. Esta consideración motiva la forma funcional saturante empleada en el motor de simulación descrito en la metodología.

## Aprendizaje automático como emulador y como instrumento explicativo

Los emuladores —*surrogates*— son modelos estadísticos entrenados para reproducir la salida de un modelo físico a una fracción del costo computacional [[REF:pradisty2025]]. En el contexto de los humedales costeros permiten explorar de manera exhaustiva el espacio de escenarios, sostener análisis de sensibilidad y alimentar interfaces interactivas.

Los ensambles de árboles —Random Forest y Extra Trees— son especialmente adecuados para esta tarea: capturan interacciones no lineales, son robustos frente a escalas heterogéneas de las variables y proveen medidas de importancia directamente interpretables [[REF:breiman2001]], [[REF:geurts2006]]. Su adopción en teledetección de manglares está ampliamente documentada [[REF:pradisty2025]].

La contrapartida de su capacidad predictiva es la opacidad. La importancia por permutación y los métodos de atribución local resuelven parcialmente este problema al cuantificar la contribución de cada variable a la predicción, y constituyen hoy un requisito práctico para la adopción de modelos en la gestión ambiental [[REF:mcNulty2025]]. No obstante, estas técnicas presentan limitaciones conocidas: la permutación puede forzar extrapolaciones fuera del soporte de los datos [[REF:hooker2019]], y su interpretación exige distinguir entre relevancia predictiva y causalidad [[REF:molnar2022]].

## Metodología CRISP-DM

CRISP-DM —*Cross-Industry Standard Process for Data Mining*— organiza un proyecto analítico en seis fases iterativas: comprensión del negocio, comprensión de los datos, preparación de los datos, modelado, evaluación y despliegue [[REF:wirth2000]]. A diferencia de aproximaciones centradas exclusivamente en el algoritmo, el estándar exige que cada artefacto analítico sea trazable hasta un objetivo de negocio explícito, y que la evaluación contemple criterios de éxito definidos *a priori*.

En aplicaciones ambientales, CRISP-DM facilita la comunicación entre equipos técnicos y gestores, y reduce el riesgo de producir modelos estadísticamente sólidos pero irrelevantes para la decisión [[REF:sadat2025]]. El presente trabajo adopta este marco y documenta cada fase con sus productos verificables.
