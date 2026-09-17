import { describe, expect, it } from "vitest";

import { computeKpis, featureLengthKm } from "@/features/sense/kpis";
import type {
  AdminProps,
  GeoFeatureCollection,
  IncidentProps,
  RoadProps,
  ShelterProps,
} from "@/lib/api";

function fc<P>(features: { geometry: { type: string; coordinates: unknown }; properties: P }[]) {
  return {
    type: "FeatureCollection",
    features: features.map((f) => ({ type: "Feature" as const, ...f })),
  } as GeoFeatureCollection<P>;
}

const point = { type: "Point", coordinates: [80, 6] };

describe("featureLengthKm", () => {
  it("measures a one-degree line as roughly 111 km", () => {
    const km = featureLengthKm({
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: [
          [80, 0],
          [81, 0],
        ],
      },
      properties: {} as RoadProps,
    });
    expect(km).toBeGreaterThan(110);
    expect(km).toBeLessThan(112);
  });
});

describe("computeKpis", () => {
  it("aggregates population, incidents, shelter capacity, and road km", () => {
    const adminLevel2 = fc<AdminProps>([
      { geometry: point, properties: { population: 100000 } as AdminProps },
      { geometry: point, properties: { population: 200000 } as AdminProps },
    ]);
    const incidents = fc<IncidentProps>([
      { geometry: point, properties: {} as IncidentProps },
      { geometry: point, properties: {} as IncidentProps },
      { geometry: point, properties: {} as IncidentProps },
    ]);
    const shelters = fc<ShelterProps>([
      { geometry: point, properties: { capacity: 50 } as ShelterProps },
      { geometry: point, properties: { capacity: null } as ShelterProps },
      { geometry: point, properties: { capacity: 100 } as ShelterProps },
    ]);
    const roads = fc<RoadProps>([
      {
        geometry: {
          type: "LineString",
          coordinates: [
            [80, 0],
            [80.5, 0],
          ],
        },
        properties: { closed: false } as RoadProps,
      },
      {
        geometry: {
          type: "LineString",
          coordinates: [
            [80, 0],
            [80.2, 0],
          ],
        },
        properties: { closed: true } as RoadProps,
      },
    ]);

    const kpis = computeKpis({ adminLevel2, incidents, shelters, roads });

    expect(kpis.districts).toBe(2);
    expect(kpis.population).toBe(300000);
    expect(kpis.incidents).toBe(3);
    expect(kpis.shelters).toBe(3);
    expect(kpis.shelterCapacityKnown).toBe(150);
    expect(kpis.shelterCapacityCount).toBe(2);
    expect(kpis.roadsKm).toBeGreaterThan(0);
    expect(kpis.closedRoadsKm).toBeGreaterThan(0);
    expect(kpis.closedRoadsKm).toBeLessThan(kpis.roadsKm);
  });

  it("returns zeroes for empty input", () => {
    const kpis = computeKpis({
      adminLevel2: undefined,
      incidents: undefined,
      shelters: undefined,
      roads: undefined,
    });
    expect(kpis.districts).toBe(0);
    expect(kpis.population).toBe(0);
    expect(kpis.roadsKm).toBe(0);
  });
});
