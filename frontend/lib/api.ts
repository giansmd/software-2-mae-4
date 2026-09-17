import type {
  User,
  Scenario,
  Measurement,
  ModelParam,
  SimulationResult,
  MLMetadata,
  MLPredictionResult,
  PredictionMethod,
  ReportFormat,
} from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("hd_token");
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  auth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const message =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : null) ||
      `Error ${res.status} en ${method} ${path}`;
    throw new ApiError(res.status, message);
  }

  return data as T;
}

const get = <T>(path: string, auth = true) =>
  request<T>("GET", path, undefined, auth);
const post = <T>(path: string, body?: unknown, auth = true) =>
  request<T>("POST", path, body, auth);
const put = <T>(path: string, body?: unknown, auth = true) =>
  request<T>("PUT", path, body, auth);
const del = <T>(path: string, auth = true) =>
  request<T>("DELETE", path, undefined, auth);

// ---------- Auth ----------
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  return post<LoginResponse>("/auth/login", { email, password }, false);
}

export async function register(params: {
  email: string;
  password: string;
  full_name: string;
  institution?: string;
}): Promise<LoginResponse> {
  return post<LoginResponse>("/auth/register", params, false);
}

export function getMe(): Promise<User> {
  return get<User>("/auth/me");
}

export function updateMe(params: {
  full_name?: string;
  email?: string;
  institution?: string;
}): Promise<User> {
  return put<User>("/auth/me", params);
}

export function changePassword(params: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  return post<void>("/auth/me/password", params);
}

// ---------- Scenarios ----------
export function getScenarios(): Promise<Scenario[]> {
  return get<Scenario[]>("/scenarios");
}

export function getScenario(id: number): Promise<Scenario> {
  return get<Scenario>(`/scenarios/${id}`);
}

export function createScenario(params: {
  name: string;
  description?: string;
  restoration_level: number;
  sea_level_rise: "low" | "medium" | "high";
  horizon_year?: number;
  baseline_area_ha?: number;
  baseline_carbon_density?: number;
  is_public?: boolean;
}): Promise<Scenario> {
  return post<Scenario>("/scenarios", params);
}

export function updateScenario(
  id: number,
  params: Partial<{
    name: string;
    description: string;
    restoration_level: number;
    sea_level_rise: "low" | "medium" | "high";
    horizon_year: number;
    baseline_area_ha: number;
    baseline_carbon_density: number;
    is_public: boolean;
  }>,
): Promise<Scenario> {
  return put<Scenario>(`/scenarios/${id}`, params);
}

export function deleteScenario(id: number): Promise<void> {
  return del<void>(`/scenarios/${id}`);
}

// ---------- Measurements ----------
export function getMeasurements(scenarioId?: number): Promise<Measurement[]> {
  const q = scenarioId ? `?scenario_id=${scenarioId}` : "";
  return get<Measurement[]>(`/measurements${q}`);
}

export function createMeasurement(params: {
  date: string;
  vegetation_cover: number;
  water_table: number;
  soil_organic_carbon: number;
  biomass: number;
  note?: string;
  scenario_id?: number;
}): Promise<Measurement> {
  return post<Measurement>("/measurements", params);
}

export function updateMeasurement(
  id: number,
  params: Partial<{
    date: string;
    vegetation_cover: number;
    water_table: number;
    soil_organic_carbon: number;
    biomass: number;
    note: string;
    scenario_id: number;
  }>,
): Promise<Measurement> {
  return put<Measurement>(`/measurements/${id}`, params);
}

export function deleteMeasurement(id: number): Promise<void> {
  return del<void>(`/measurements/${id}`);
}

// ---------- Model params ----------
export function getModelParams(): Promise<ModelParam[]> {
  return get<ModelParam[]>("/model-params");
}

export function updateModelParam(
  key: string,
  value: number,
): Promise<ModelParam> {
  return put<ModelParam>(`/model-params/${key}`, { value });
}

// ---------- Simulations ----------
export function runSimulation(params: {
  scenario_id?: number;
  restoration_level?: number;
  sea_level_rise?: "low" | "medium" | "high";
  horizon_year?: number;
  baseline_area_ha?: number;
  baseline_carbon_density?: number;
  scenario_name?: string;
  method?: PredictionMethod;
}): Promise<SimulationResult> {
  return post<SimulationResult>("/simulations/run", params);
}

export function getSimulation(
  scenarioId: number,
  method: PredictionMethod = "engine",
): Promise<SimulationResult> {
  return get<SimulationResult>(`/simulations/${scenarioId}?method=${method}`);
}

// ---------- ML surrogate model ----------
export function getMLMetadata(): Promise<MLMetadata> {
  return get<MLMetadata>("/ml/metadata", false);
}

export function predictML(params: {
  scenario_id?: number;
  restoration_level?: number;
  sea_level_rise?: "low" | "medium" | "high";
  horizon_year?: number;
  baseline_area_ha?: number;
  baseline_carbon_density?: number;
}): Promise<MLPredictionResult> {
  return post<MLPredictionResult>("/ml/predict", params, false);
}

// ---------- Reports ----------
export async function downloadReport(
  scenarioId: number,
  fmt: ReportFormat,
  method: PredictionMethod = "engine",
): Promise<void> {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/reports/${scenarioId}/${fmt}?method=${method}`,
    token ? { headers: { Authorization: `Bearer ${token}` } } : {},
  );
  if (!res.ok) {
    throw new ApiError(res.status, `Error descargando reporte ${fmt}`);
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `reporte_${scenarioId}.${fmt}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ---------- Users (ADMIN) ----------
export function getUsers(): Promise<User[]> {
  return get<User[]>("/users");
}

export function createUser(params: {
  email: string;
  password: string;
  full_name: string;
  institution?: string;
  role: "ADMIN" | "INVESTIGADOR" | "VISITANTE";
}): Promise<User> {
  return post<User>("/users", params);
}

export function deleteUser(id: number): Promise<void> {
  return del<void>(`/users/${id}`);
}

// ---------- Util ----------
export function errMessage(e: unknown): string {
  if (e instanceof Error) return e.message;
  if (typeof e === "string") return e;
  if (e && typeof e === "object" && "message" in e) {
    return String((e as { message: unknown }).message);
  }
  return String(e);
}

// ---------- Health ----------
export function getHealth(): Promise<{ status: string; service: string }> {
  return get<{ status: string; service: string }>("/health", false);
}
