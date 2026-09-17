import "maplibre-gl/dist/maplibre-gl.css";

import maplibregl from "maplibre-gl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAdminRegions, useHazardLayers, useShelters } from "@/features/sense/hooks";
import { basemapStyle } from "@/features/sense/map/basemap";
import { readMapColors, withAlpha } from "@/features/sense/mapColors";
import type { GeoFeatureCollection, ShelterProps } from "@/lib/api";
import type { Theme } from "@/store/ui";

const EMPTY: GeoFeatureCollection<unknown> = { type: "FeatureCollection", features: [] };

interface BuilderMapProps {
  slug: string;
  theme: Theme;
  bbox: [number, number, number, number] | null;
  priorityPcodes: string[];
  activatedShelterIds: number[];
}

/**
 * A lightweight context map for the builder: flood extent, admin regions (with
 * the priority set highlighted), and the activated shelters — so lever choices
 * are spatial, not abstract. Reuses the shared layer queries + token colors.
 */
export function BuilderMap({
  slug,
  theme,
  bbox,
  priorityPcodes,
  activatedShelterIds,
}: BuilderMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [epoch, setEpoch] = useState(0);

  const admin = useAdminRegions(slug, 2);
  const hazards = useHazardLayers(slug);
  const shelters = useShelters(slug);

  const flood = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: (hazards.data?.features ?? []).filter(
        (f) => f.properties.layer_type === "flood_extent",
      ),
    }),
    [hazards.data],
  );

  const activatedShelters = useMemo(() => {
    const ids = new Set(activatedShelterIds);
    const features = (shelters.data?.features ?? []).filter((f) =>
      ids.has((f.properties as ShelterProps).id),
    );
    return { type: "FeatureCollection" as const, features };
  }, [shelters.data, activatedShelterIds]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: run-once map lifecycle
  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: basemapStyle(theme),
      center: [80.4, 6.6],
      zoom: 7.5,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.on("style.load", () => setEpoch((e) => e + 1));
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Add sources + layers once the style is ready.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0) return;
    const colors = readMapColors();
    const ensureSource = (id: string) => {
      if (!map.getSource(id)) {
        map.addSource(id, { type: "geojson", data: EMPTY as GeoJSON.FeatureCollection });
      }
    };
    for (const id of ["bm-admin", "bm-flood", "bm-shelters"]) ensureSource(id);

    if (!map.getLayer("bm-admin-priority")) {
      map.addLayer({
        id: "bm-admin-priority",
        type: "fill",
        source: "bm-admin",
        paint: { "fill-color": withAlpha(colors, "primary", 0.28) },
        filter: ["in", ["get", "pcode"], ["literal", []]],
      });
    }
    if (!map.getLayer("bm-admin-line")) {
      map.addLayer({
        id: "bm-admin-line",
        type: "line",
        source: "bm-admin",
        paint: { "line-color": withAlpha(colors, "muted-foreground", 0.5), "line-width": 0.6 },
      });
    }
    if (!map.getLayer("bm-flood-fill")) {
      map.addLayer({
        id: "bm-flood-fill",
        type: "fill",
        source: "bm-flood",
        paint: { "fill-color": withAlpha(colors, "signal-info", 0.35) },
      });
    }
    if (!map.getLayer("bm-shelters")) {
      map.addLayer({
        id: "bm-shelters",
        type: "circle",
        source: "bm-shelters",
        paint: {
          "circle-color": colors["signal-ok"],
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 7, 2.5, 13, 5],
          "circle-stroke-width": 0.5,
          "circle-stroke-color": withAlpha(colors, "background", 0.8),
        },
      });
    }
  }, [epoch]);

  const setData = useCallback((id: string, fc: GeoFeatureCollection<unknown>) => {
    const src = mapRef.current?.getSource(id) as maplibregl.GeoJSONSource | undefined;
    if (src) src.setData(fc as GeoJSON.FeatureCollection);
  }, []);

  useEffect(() => {
    if (epoch === 0) return;
    if (admin.data) setData("bm-admin", admin.data);
  }, [epoch, admin.data, setData]);
  useEffect(() => {
    if (epoch !== 0) setData("bm-flood", flood);
  }, [epoch, flood, setData]);
  useEffect(() => {
    if (epoch !== 0) setData("bm-shelters", activatedShelters);
  }, [epoch, activatedShelters, setData]);

  // Highlight the priority regions.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0 || !map.getLayer("bm-admin-priority")) return;
    map.setFilter("bm-admin-priority", ["in", ["get", "pcode"], ["literal", priorityPcodes]]);
  }, [epoch, priorityPcodes]);

  // Fit to the scenario bbox.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !bbox) return;
    const fit = () =>
      map.fitBounds(
        [
          [bbox[0], bbox[1]],
          [bbox[2], bbox[3]],
        ],
        { padding: 24, duration: 500 },
      );
    if (map.isStyleLoaded()) fit();
    else map.once("load", fit);
  }, [bbox]);

  return <div ref={containerRef} className="h-full w-full" aria-label="Context map" />;
}
