# Dataset híbrido MAE-4

Covariables reales publicadas del SNLMT y variable objetivo generada por el motor
determinista. Semillas 42 (modelado) y 43 (holdout independiente), horizonte 2050.

Atributos del modelo: restoration_level, sea_level_rise_code, horizon_year, baseline_area_ha, baseline_carbon_density, ndvi.
Objetivo: horizon_variation_pct.

Incluye una muestra de trayectorias anuales del motor (2020-2050) sobre una
línea base de 100 ha y 80 tC/ha.

Regenerar con `paper/regenerate_v2.py` (figuras y tablas) o `paper/export_dataset.py`
(este paquete). Licencia del software: MIT. GMW v3.0: CC BY 4.0.
