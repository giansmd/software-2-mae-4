import type { LiveValues } from "@/lib/types";

export const TERRAIN_SIZE = 10;
export const TERRAIN_HEIGHT = 0.9;
export const MAX_VEGETATION = 3000;

const BASE_LAND_FRACTION = 0.72;
const REFERENCE_CARBON_DENSITY = 85;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function rawHeight(u: number, v: number): number {
  return (
    0.42 * Math.sin(u * 3.1 + 0.7) * Math.cos(v * 2.7 - 1.1) +
    0.22 * Math.sin(u * 6.3 - 2.0) * Math.sin(v * 5.1 + 0.4) +
    0.1 * Math.cos(u * 11.0 + v * 9.0)
  );
}

export function terrainHeight(x: number, z: number): number {
  const u = (x / TERRAIN_SIZE) * 2;
  const v = (z / TERRAIN_SIZE) * 2;
  return rawHeight(u, v) * TERRAIN_HEIGHT;
}

const TERRAIN_SAMPLES: number[] = (() => {
  const n = 40;
  const samples: number[] = [];
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      const x = -TERRAIN_SIZE / 2 + (TERRAIN_SIZE * i) / (n - 1);
      const z = -TERRAIN_SIZE / 2 + (TERRAIN_SIZE * j) / (n - 1);
      samples.push(terrainHeight(x, z));
    }
  }
  samples.sort((a, b) => a - b);
  return samples;
})();

export function waterLevelForLandFraction(fraction: number): number {
  const f = clamp(fraction, 0, 1);
  const index = Math.round((1 - f) * (TERRAIN_SAMPLES.length - 1));
  return TERRAIN_SAMPLES[index];
}

export interface VegetationInstance {
  x: number;
  y: number;
  z: number;
  rotation: number;
  scale: number;
}

function mulberry32(seed: number): () => number {
  let state = seed;
  return () => {
    state |= 0;
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const VEGETATION_LAYOUT: VegetationInstance[] = (() => {
  const random = mulberry32(20250916);
  const list: VegetationInstance[] = [];
  for (let i = 0; i < MAX_VEGETATION * 3 && list.length < MAX_VEGETATION; i++) {
    const x = (random() - 0.5) * TERRAIN_SIZE * 0.96;
    const z = (random() - 0.5) * TERRAIN_SIZE * 0.96;
    const y = terrainHeight(x, z);
    list.push({
      x,
      y,
      z,
      rotation: random() * Math.PI * 2,
      scale: 0.6 + random() * 0.8,
    });
  }
  list.sort((a, b) => b.y - a.y);
  return list;
})();

export interface WetlandBaseline {
  areaHa: number;
  carbonDensity: number;
}

export interface WetlandSceneParams {
  waterLevel: number;
  landFraction: number;
  vegetationDensity: number;
  vegetationHealth: number;
  carbonLevel: number;
  variationPct: number;
  waterTable: number;
}

export const IDLE_SCENE_PARAMS: WetlandSceneParams = {
  waterLevel: waterLevelForLandFraction(BASE_LAND_FRACTION),
  landFraction: BASE_LAND_FRACTION,
  vegetationDensity: 0.5,
  vegetationHealth: 0.7,
  carbonLevel: 0.4,
  variationPct: 0,
  waterTable: -0.1,
};

export function buildSceneParams(
  values: LiveValues | null,
  baseline?: WetlandBaseline | null,
): WetlandSceneParams {
  if (!values) return IDLE_SCENE_PARAMS;

  const areaRatio =
    baseline && baseline.areaHa > 0
      ? clamp(values.effective_area_ha / baseline.areaHa, 0, 1.2)
      : 1;
  const landFraction = clamp(BASE_LAND_FRACTION * areaRatio, 0.05, 0.98);
  const waterTableDelta = clamp((values.water_table + 0.1) * 0.4, -0.03, 0.03);
  const waterLevel =
    waterLevelForLandFraction(landFraction) + waterTableDelta;

  const referenceDensity =
    baseline && baseline.carbonDensity > 0
      ? baseline.carbonDensity
      : REFERENCE_CARBON_DENSITY;

  return {
    waterLevel,
    landFraction,
    vegetationDensity: clamp(values.vegetation_cover, 0, 1),
    vegetationHealth: clamp(values.soil_organic_carbon / referenceDensity, 0, 1),
    carbonLevel: clamp((values.variation_pct + 30) / 80, 0, 1),
    variationPct: values.variation_pct,
    waterTable: values.water_table,
  };
}
