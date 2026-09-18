import "maplibre-gl/dist/maplibre-gl.css";

import maplibregl from "maplibre-gl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAdminRegions, useHazardLayers } from "@/features/sense/hooks";
import { basemapStyle } from "@/features/sense/map/basemap";
import { readMapColors, withAlpha } from "@/features/sense/mapColors";
import type { GeoFeatureCollection } from "@/lib/api";
import type { Theme } from "@/store/ui";

const EMPTY: GeoFeatureCollection<unknown> = { type: "FeatureCollection", features: [] };

interface LearnMapProps {
  slug: string;
  theme: Theme;
  bbox: [number, number, number, number] | null;
  /** pcode -> recorded composite impact (0..100). */
  impactByPcode: Record<string, number>;
  priorityPcodes: string[];
}

/**
 * A recorded-impact choropleth: districts shaded by their ACTUAL recorded impact
 * (real DesInventar), with the strategy's priority districts outlined — so the
 * predicted-vs-recorded mismatch is spatial. Reuses the shared layer queries and
 * token colours (Builder/Sense map pattern).
 */
export function LearnMap({ slug, theme, bbox, impactByPcode, priorityPcodes }: LearnMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [epoch, setEpoch] = useState(0);

  const admin = useAdminRegions(slug, 2);
  const hazards = useHazardLayers(slug);

  const flood = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: (hazards.data?.features ?? []).filter(
        (f) => f.properties.layer_type === "flood_extent",
      ),
    }),
    [hazards.data],
  );

  // Inject recorded impact into each district feature so a data-driven fill can
  // shade it. Districts with no recorded impact fall to 0 (near-transparent).
  const adminWithImpact = useMemo(() => {
    if (!admin.data) return EMPTY;
    return {
      type: "FeatureCollection" as const,
      features: admin.data.features.map((f) => ({
        ...f,
        properties: { ...f.properties, impact: impactByPcode[f.properties.pcode] ?? 0 },
      })),
    };
  }, [admin.data, impactByPcode]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: run-once map lifecycle
  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: basemapStyle(theme),
      center: [80.4, 6.6],
      zoom: 7.3,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.on("style.load", () => setEpoch((e) => e + 1));
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0) return;
    const colors = readMapColors();
    const ensureSource = (id: string) => {
      if (!map.getSource(id)) {
        map.addSource(id, { type: "geojson", data: EMPTY as GeoJSON.FeatureCollection });
      }
    };
    for (const id of ["lm-admin", "lm-flood"]) ensureSource(id);

    if (!map.getLayer("lm-impact-fill")) {
      map.addLayer({
        id: "lm-impact-fill",
        type: "fill",
        source: "lm-admin",
        paint: {
          "fill-color": [
            "interpolate",
            ["linear"],
            ["get", "impact"],
            0,
            withAlpha(colors, "signal-crit", 0.04),
            25,
            withAlpha(colors, "signal-crit", 0.25),
            60,
            withAlpha(colors, "signal-crit", 0.5),
            100,
            withAlpha(colors, "signal-crit", 0.8),
          ],
        },
      });
    }
    if (!map.getLayer("lm-flood-fill")) {
      map.addLayer({
        id: "lm-flood-fill",
        type: "fill",
        source: "lm-flood",
        paint: { "fill-color": withAlpha(colors, "signal-info", 0.14) },
      });
    }
    if (!map.getLayer("lm-priority-line")) {
      map.addLayer({
        id: "lm-priority-line",
        type: "line",
        source: "lm-admin",
        paint: { "line-color": colors.primary, "line-width": 2 },
        filter: ["in", ["get", "pcode"], ["literal", []]],
      });
    }
    if (!map.getLayer("lm-admin-line")) {
      map.addLayer({
        id: "lm-admin-line",
        type: "line",
        source: "lm-admin",
        paint: { "line-color": withAlpha(colors, "muted-foreground", 0.4), "line-width": 0.5 },
      });
    }
  }, [epoch]);

  const setData = useCallback((id: string, fc: GeoFeatureCollection<unknown>) => {
    const src = mapRef.current?.getSource(id) as maplibregl.GeoJSONSource | undefined;
    if (src) src.setData(fc as GeoJSON.FeatureCollection);
  }, []);

  useEffect(() => {
    if (epoch !== 0) setData("lm-admin", adminWithImpact);
  }, [epoch, adminWithImpact, setData]);
  useEffect(() => {
    if (epoch !== 0) setData("lm-flood", flood);
  }, [epoch, flood, setData]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0 || !map.getLayer("lm-priority-line")) return;
    map.setFilter("lm-priority-line", ["in", ["get", "pcode"], ["literal", priorityPcodes]]);
  }, [epoch, priorityPcodes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !bbox) return;
    const fit = () =>
      map.fitBounds(
        [
          [bbox[0], bbox[1]],
          [bbox[2], bbox[3]],
        ],
        { padding: 20, duration: 400 },
      );
    if (map.isStyleLoaded()) fit();
    else map.once("load", fit);
  }, [bbox]);

  return <div ref={containerRef} className="h-full w-full" aria-label="Recorded impact map" />;
}
