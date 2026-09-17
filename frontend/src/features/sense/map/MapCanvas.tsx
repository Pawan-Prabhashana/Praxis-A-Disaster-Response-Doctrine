import "maplibre-gl/dist/maplibre-gl.css";

import maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";

import type { LayerKey } from "@/features/sense/layers";
import { basemapStyle } from "@/features/sense/map/basemap";
import { type MapColors, readMapColors, withAlpha } from "@/features/sense/mapColors";
import type { SelectedFeature } from "@/features/sense/store";
import type {
  AdminProps,
  GeoFeatureCollection,
  HazardProps,
  IncidentProps,
  RiverProps,
  RoadProps,
  ShelterProps,
} from "@/lib/api";
import type { Theme } from "@/store/ui";

const EMPTY_FC: GeoFeatureCollection<never> = { type: "FeatureCollection", features: [] };

// Layer id → source id, and which store LayerKey controls its visibility.
const LAYER_VISIBILITY: Record<LayerKey, string[]> = {
  admin: ["admin-fill", "admin-line"],
  flood: ["flood-fill", "flood-line"],
  landslide: ["landslide-fill", "landslide-line"],
  roads: ["roads-line", "roads-closed"],
  shelters: ["shelter-clusters", "shelter-cluster-count", "shelter-point"],
  incidents: ["incidents-circle"],
  rivers: ["rivers-circle"],
};

export interface MapData {
  admin?: GeoFeatureCollection<AdminProps> | undefined;
  flood?: GeoFeatureCollection<HazardProps> | undefined;
  landslide?: GeoFeatureCollection<HazardProps> | undefined;
  roads?: GeoFeatureCollection<RoadProps> | undefined;
  shelters?: GeoFeatureCollection<ShelterProps> | undefined;
  incidents?: GeoFeatureCollection<IncidentProps> | undefined;
  rivers?: GeoFeatureCollection<RiverProps> | undefined;
}

interface MapCanvasProps {
  theme: Theme;
  bbox: [number, number, number, number] | null;
  visibility: Record<LayerKey, boolean>;
  data: MapData;
  selected: SelectedFeature | null;
  onSelect: (feature: SelectedFeature) => void;
  onClearSelection: () => void;
}

function setData(map: maplibregl.Map, id: string, fc: GeoFeatureCollection<unknown> | undefined) {
  const source = map.getSource(id) as maplibregl.GeoJSONSource | undefined;
  if (source) source.setData((fc ?? EMPTY_FC) as GeoJSON.FeatureCollection);
}

/** Add every source + layer if missing, and (re)apply theme colors. Idempotent. */
function ensureLayers(map: maplibregl.Map, colors: MapColors): void {
  const addSource = (id: string, cluster = false) => {
    if (!map.getSource(id)) {
      map.addSource(id, {
        type: "geojson",
        data: EMPTY_FC as GeoJSON.FeatureCollection,
        ...(cluster ? { cluster: true, clusterRadius: 48, clusterMaxZoom: 12 } : {}),
      });
    }
  };

  for (const id of ["admin", "flood", "landslide", "roads", "incidents", "rivers", "selection"]) {
    addSource(`src-${id}`);
  }
  addSource("src-shelters", true);

  const add = (layer: maplibregl.LayerSpecification) => {
    if (!map.getLayer(layer.id)) map.addLayer(layer);
  };

  // --- Admin choropleth (by population) ---
  add({
    id: "admin-fill",
    type: "fill",
    source: "src-admin",
    paint: {
      "fill-color": [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", "population"], 0],
        0,
        withAlpha(colors, "primary", 0.05),
        250000,
        withAlpha(colors, "primary", 0.18),
        600000,
        withAlpha(colors, "primary", 0.34),
        1200000,
        withAlpha(colors, "primary", 0.55),
      ],
    },
  });
  add({
    id: "admin-line",
    type: "line",
    source: "src-admin",
    paint: { "line-color": withAlpha(colors, "muted-foreground", 0.5), "line-width": 0.6 },
  });

  // --- Flood extent (real) ---
  add({
    id: "flood-fill",
    type: "fill",
    source: "src-flood",
    paint: { "fill-color": withAlpha(colors, "signal-info", 0.35) },
  });
  add({
    id: "flood-line",
    type: "line",
    source: "src-flood",
    paint: { "line-color": colors["signal-info"], "line-width": 0.8, "line-opacity": 0.8 },
  });

  // --- Landslide susceptibility (SYNTHETIC: translucent + dashed outline) ---
  add({
    id: "landslide-fill",
    type: "fill",
    source: "src-landslide",
    paint: {
      "fill-color": [
        "interpolate",
        ["linear"],
        ["coalesce", ["get", "severity_class"], 1],
        1,
        withAlpha(colors, "signal-warn", 0.12),
        3,
        withAlpha(colors, "signal-warn", 0.3),
      ],
    },
  });
  add({
    id: "landslide-line",
    type: "line",
    source: "src-landslide",
    paint: {
      "line-color": colors["signal-warn"],
      "line-width": 1,
      "line-dasharray": [2, 2],
      "line-opacity": 0.7,
    },
  });

  // --- Roads (base subtle; closed emphasized + dashed = synthetic) ---
  add({
    id: "roads-line",
    type: "line",
    source: "src-roads",
    paint: {
      "line-color": withAlpha(colors, "muted-foreground", 0.55),
      "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.4, 14, 1.6],
    },
  });
  add({
    id: "roads-closed",
    type: "line",
    source: "src-roads",
    filter: ["==", ["get", "closed"], true],
    paint: {
      "line-color": colors["signal-crit"],
      "line-width": ["interpolate", ["linear"], ["zoom"], 8, 1.2, 14, 3],
      "line-dasharray": [1.5, 1.5],
    },
  });

  // --- Incidents (real; DesInventar vs GDACS by color) ---
  add({
    id: "incidents-circle",
    type: "circle",
    source: "src-incidents",
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 7, 2.2, 13, 5],
      "circle-color": [
        "case",
        ["in", "GDACS", ["get", "source"]],
        colors["signal-info"],
        colors["signal-warn"],
      ],
      "circle-opacity": 0.65,
      "circle-stroke-width": 0.4,
      "circle-stroke-color": withAlpha(colors, "background", 0.8),
    },
  });

  // --- Shelters (clustered) ---
  add({
    id: "shelter-clusters",
    type: "circle",
    source: "src-shelters",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": withAlpha(colors, "signal-ok", 0.75),
      "circle-radius": ["step", ["get", "point_count"], 12, 25, 16, 100, 22],
      "circle-stroke-width": 1,
      "circle-stroke-color": withAlpha(colors, "background", 0.7),
    },
  });
  add({
    id: "shelter-cluster-count",
    type: "symbol",
    source: "src-shelters",
    filter: ["has", "point_count"],
    layout: {
      "text-field": ["get", "point_count_abbreviated"],
      "text-font": ["Open Sans Semibold"],
      "text-size": 11,
    },
    paint: { "text-color": colors["signal-ok-foreground"] },
  });
  add({
    id: "shelter-point",
    type: "circle",
    source: "src-shelters",
    filter: ["!", ["has", "point_count"]],
    paint: {
      "circle-color": colors["signal-ok"],
      "circle-radius": 4,
      "circle-stroke-width": 0.6,
      "circle-stroke-color": withAlpha(colors, "background", 0.8),
    },
  });

  // --- Rivers ---
  add({
    id: "rivers-circle",
    type: "circle",
    source: "src-rivers",
    paint: {
      "circle-color": colors["signal-info"],
      "circle-radius": 6,
      "circle-stroke-width": 2,
      "circle-stroke-color": withAlpha(colors, "foreground", 0.9),
    },
  });

  // --- Selection halo (top) ---
  add({
    id: "selection-halo",
    type: "circle",
    source: "src-selection",
    paint: {
      "circle-radius": 12,
      "circle-color": "rgba(0,0,0,0)",
      "circle-stroke-width": 2.5,
      "circle-stroke-color": colors.primary,
    },
  });
}

function setSelectionHalo(map: maplibregl.Map, geometry: GeoJSON.Geometry | null): void {
  const features =
    geometry && geometry.type === "Point"
      ? [{ type: "Feature" as const, geometry, properties: {} }]
      : [];
  const src = map.getSource("src-selection") as maplibregl.GeoJSONSource | undefined;
  if (src) src.setData({ type: "FeatureCollection", features });
}

export function MapCanvas({
  theme,
  bbox,
  visibility,
  data,
  selected,
  onSelect,
  onClearSelection,
}: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [epoch, setEpoch] = useState(0);

  // Create the map once. The component is remounted (via a `key={theme}` at the
  // call site) when the theme changes, so the basemap is always created with the
  // correct style — no setStyle race. `onSelect` is a stable Zustand action.
  // biome-ignore lint/correctness/useExhaustiveDependencies: run-once map lifecycle
  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: basemapStyle(theme),
      center: [80.4, 6.6],
      zoom: 8,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    // `style.load` fires on initial load and after every setStyle → re-add layers.
    map.on("style.load", () => setEpoch((e) => e + 1));

    const clickable = ["incidents-circle", "shelter-point", "rivers-circle", "admin-fill"] as const;
    for (const layer of clickable) {
      map.on("mouseenter", layer, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", layer, () => {
        map.getCanvas().style.cursor = "";
      });
    }

    // Single click handler with explicit priority. Point features win over the
    // admin polygon beneath them (separate per-layer handlers would all fire and
    // the last-registered one would clobber the selection).
    map.on("click", (e) => {
      const priority = [
        "shelter-clusters",
        "rivers-circle",
        "incidents-circle",
        "shelter-point",
        "admin-fill",
      ].filter((id) => map.getLayer(id));
      const feats = map.queryRenderedFeatures(e.point, { layers: priority });
      if (feats.length === 0) return;
      const pick = (id: string) => feats.find((f) => f.layer.id === id);

      const cluster = pick("shelter-clusters");
      if (cluster) {
        const clusterId = cluster.properties?.cluster_id;
        const src = map.getSource("src-shelters") as maplibregl.GeoJSONSource | undefined;
        if (clusterId != null && src) {
          void src.getClusterExpansionZoom(clusterId).then((zoom) => {
            const geom = cluster.geometry as GeoJSON.Point;
            map.easeTo({ center: geom.coordinates as [number, number], zoom: zoom + 0.5 });
          });
        }
        return;
      }

      const river = pick("rivers-circle");
      if (river) {
        onSelect({ kind: "river", props: river.properties as unknown as RiverProps });
        setSelectionHalo(map, river.geometry);
        return;
      }
      const incident = pick("incidents-circle");
      if (incident) {
        onSelect({ kind: "incident", props: incident.properties as unknown as IncidentProps });
        setSelectionHalo(map, incident.geometry);
        return;
      }
      const shelter = pick("shelter-point");
      if (shelter) {
        onSelect({ kind: "shelter", props: shelter.properties as unknown as ShelterProps });
        setSelectionHalo(map, shelter.geometry);
        return;
      }
      const admin = pick("admin-fill");
      if (admin) {
        onSelect({ kind: "admin", props: admin.properties as unknown as AdminProps });
        setSelectionHalo(map, null);
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // (Re)create sources + layers whenever the base style (re)loads.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0) return;
    ensureLayers(map, readMapColors());
  }, [epoch]);

  // Push data into sources.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0) return;
    setData(map, "src-admin", data.admin);
    setData(map, "src-flood", data.flood);
    setData(map, "src-landslide", data.landslide);
    setData(map, "src-roads", data.roads);
    setData(map, "src-shelters", data.shelters);
    setData(map, "src-incidents", data.incidents);
    setData(map, "src-rivers", data.rivers);
  }, [epoch, data]);

  // Apply layer visibility.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0) return;
    for (const [key, layerIds] of Object.entries(LAYER_VISIBILITY)) {
      const visible = visibility[key as LayerKey];
      for (const id of layerIds) {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
        }
      }
    }
  }, [epoch, visibility]);

  // Clear the selection halo when the selection is cleared externally.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || epoch === 0) return;
    if (selected === null) setSelectionHalo(map, null);
  }, [epoch, selected]);

  // Fit to the scenario bbox on load / scenario change.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !bbox) return;
    const fit = () =>
      map.fitBounds(
        [
          [bbox[0], bbox[1]],
          [bbox[2], bbox[3]],
        ],
        { padding: 48, duration: 600 },
      );
    if (map.isStyleLoaded()) fit();
    else map.once("load", fit);
  }, [bbox]);

  return (
    <div className="relative h-full w-full">
      <div
        ref={containerRef}
        className="h-full w-full"
        role="application"
        aria-label="Operational map"
        onKeyDown={(e) => {
          if (e.key === "Escape") onClearSelection();
        }}
      />
    </div>
  );
}
