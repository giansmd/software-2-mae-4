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

export interface SimulationResult {
  scenario_id: number | null;
  scenario_name: string;
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
  series: SeriesPoint[];
}

export type ReportFormat = "pdf" | "docx" | "xlsx";
