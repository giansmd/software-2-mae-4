export type Role = "ADMIN" | "INVESTIGADOR" | "VISITANTE";
export type SeaLevelRise = "low" | "medium" | "high";

export interface User {
  id: number;
  email: string;
  full_name: string;
  institution: string | null;
  role: Role;
  is_active: boolean;
}

export interface Scenario {
  id: number;
  name: string;
  description: string | null;
  owner_id: number | null;
  restoration_level: number;
  sea_level_rise: SeaLevelRise;
  horizon_year: number;
  baseline_area_ha: number;
  baseline_carbon_density: number;
  is_public: boolean;
}

export interface Measurement {
  id: number;
  scenario_id: number | null;
  owner_id: number | null;
  date: string;
  vegetation_cover: number;
  water_table: number;
  soil_organic_carbon: number;
  biomass: number;
  note: string | null;
}

export interface ModelParam {
  key: string;
  value: number;
  unit: string | null;
  description: string | null;
}

export interface SeriesPoint {
  year: number;
  retained_carbon: number;
  effective_area_ha: number;
  vegetation_cover: number;
  variation_pct: number;
}

export type PredictionMethod = "engine" | "ml" | "ensemble";

export interface SimulationResult {
  scenario_id: number | null;
  scenario_name: string;
  method: PredictionMethod;
  restoration_level: number;
  sea_level_rise: SeaLevelRise;
  horizon_year: number;
  baseline_area_ha: number;
  baseline_carbon_density: number;
  baseline_carbon: number;
  horizon_carbon: number;
  horizon_variation_pct: number;
  meets_hypothesis: boolean;
  hypothesis_threshold_pct: number;
  engine_horizon_variation_pct: number;
  engine_horizon_carbon: number;
  engine_meets_hypothesis: boolean;
  ml_horizon_variation_pct: number | null;
  ml_horizon_carbon: number | null;
  ml_meets_hypothesis: boolean | null;
  series: SeriesPoint[];
}

export interface RegressionMetrics {
  r2_variation: number;
  mae_variation: number;
  rmse_variation: number;
  r2_carbon: number;
  mae_carbon: number;
  rmse_carbon: number;
  cv_r2_mean: number;
  cv_r2_std: number;
}

export interface ClassificationMetrics {
  accuracy: number;
  roc_auc: number;
}

export interface MLMetadata {
  algorithm: string;
  model_version: string;
  data_source: string;
  trained_at: string;
  n_samples: number;
  n_train: number;
  n_test: number;
  feature_names: string[];
  feature_importances: Record<string, number>;
  regression: RegressionMetrics;
  classification: ClassificationMetrics;
}

export interface MLPredictionResult {
  scenario_id: number | null;
  scenario_name: string;
  restoration_level: number;
  sea_level_rise: SeaLevelRise;
  horizon_year: number;
  baseline_area_ha: number;
  baseline_carbon_density: number;
  ml_variation_pct: number;
  ml_horizon_carbon: number;
  ml_meets_hypothesis: boolean;
  ml_meets_hypothesis_probability: number;
  engine_variation_pct: number;
  engine_horizon_carbon: number;
  engine_meets_hypothesis: boolean;
  delta_variation_pct: number;
  hypothesis_threshold_pct: number;
}

export type ReportFormat = "pdf" | "docx" | "xlsx";

export interface LiveValues {
  water_table: number;
  vegetation_cover: number;
  soil_organic_carbon: number;
  biomass: number;
  retained_carbon: number;
  effective_area_ha: number;
  variation_pct: number;
}

export interface LiveStateMessage {
  type: "state";
  sequence: number;
  timestamp: string;
  virtual_time: string;
  source: "simulated";
  values: LiveValues;
}

export type LiveServerMessage =
  | LiveStateMessage
  | { type: "status"; status: string; value?: number }
  | { type: "error"; message: string };
