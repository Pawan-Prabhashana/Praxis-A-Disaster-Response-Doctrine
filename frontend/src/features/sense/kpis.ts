/**
 * Pure KPI computation from loaded FeatureCollections. No React, no network —
 * unit-tested directly. Every KPI traces to real loaded data; the closed-roads
 * figure is derived from the (synthetic) closure flag and is marked as sample
 * in the UI.
 */

import type {
  AdminProps,
  GeoFeature,
  GeoFeatureCollection,
  IncidentProps,
  RoadProps,
  ShelterProps,
} from "@/lib/api";

export interface SenseKpis {
  districts: number;
  population: number;
  incidents: number;
  shelters: number;
  shelterCapacityKnown: number;
  shelterCapacityCount: number;
  roadsKm: number;
  closedRoadsKm: number;
}

const EARTH_RADIUS_KM = 6371;

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function haversineKm(a: [number, number], b: [number, number]): number {
  const dLat = toRad(b[1] - a[1]);
  const dLon = toRad(b[0] - a[0]);
  const lat1 = toRad(a[1]);
  const lat2 = toRad(b[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.sin(dLon / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2);
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(h));
}

/** Length in km of a GeoJSON LineString / MultiLineString feature. */
export function featureLengthKm(feature: GeoFeature<RoadProps>): number {
  const { type, coordinates } = feature.geometry;
  const lines: number[][][] =
    type === "MultiLineString"
      ? (coordinates as number[][][])
      : type === "LineString"
        ? [coordinates as number[][]]
        : [];
  let total = 0;
  for (const line of lines) {
    for (let i = 1; i < line.length; i++) {
      const prev = line[i - 1];
      const cur = line[i];
      if (prev && cur) {
        total += haversineKm([prev[0] ?? 0, prev[1] ?? 0], [cur[0] ?? 0, cur[1] ?? 0]);
      }
    }
  }
  return total;
}

export function computeKpis(input: {
  adminLevel2: GeoFeatureCollection<AdminProps> | undefined;
  incidents: GeoFeatureCollection<IncidentProps> | undefined;
  shelters: GeoFeatureCollection<ShelterProps> | undefined;
  roads: GeoFeatureCollection<RoadProps> | undefined;
}): SenseKpis {
  const adminFeatures = input.adminLevel2?.features ?? [];
  const shelterFeatures = input.shelters?.features ?? [];
  const roadFeatures = input.roads?.features ?? [];

  const capacities = shelterFeatures
    .map((f) => f.properties.capacity)
    .filter((c): c is number => typeof c === "number");

  let roadsKm = 0;
  let closedRoadsKm = 0;
  for (const road of roadFeatures) {
    const km = featureLengthKm(road);
    roadsKm += km;
    if (road.properties.closed) closedRoadsKm += km;
  }

  return {
    districts: adminFeatures.length,
    population: adminFeatures.reduce((sum, f) => sum + (f.properties.population ?? 0), 0),
    incidents: input.incidents?.features.length ?? 0,
    shelters: shelterFeatures.length,
    shelterCapacityKnown: capacities.reduce((a, b) => a + b, 0),
    shelterCapacityCount: capacities.length,
    roadsKm,
    closedRoadsKm,
  };
}
