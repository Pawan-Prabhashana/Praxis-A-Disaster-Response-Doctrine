import { AlertTriangle, Layers3, PanelRightOpen } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  useAdminRegions,
  useHazardLayers,
  useIncidents,
  useRivers,
  useRoads,
  useScenarioDetail,
  useShelters,
} from "@/features/sense/hooks";
import { computeKpis } from "@/features/sense/kpis";
import type { LayerKey } from "@/features/sense/layers";
import { MapCanvas, type MapData } from "@/features/sense/map/MapCanvas";
import { ContextPanel } from "@/features/sense/panels/ContextPanel";
import { KpiStrip } from "@/features/sense/panels/KpiStrip";
import { LayerPanel } from "@/features/sense/panels/LayerPanel";
import { useSenseStore } from "@/features/sense/store";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

export function SenseDashboard() {
  const { t } = useTranslation();
  const theme = useUiStore((s) => s.theme);
  const slug = useUiStore((s) => s.selectedScenarioSlug);

  const visibility = useSenseStore((s) => s.visibility);
  const toggleLayer = useSenseStore((s) => s.toggleLayer);
  const adminLevel = useSenseStore((s) => s.adminLevel);
  const setAdminLevel = useSenseStore((s) => s.setAdminLevel);
  const selected = useSenseStore((s) => s.selected);
  const select = useSenseStore((s) => s.select);
  const clearSelection = useSenseStore((s) => s.clearSelection);

  const detail = useScenarioDetail(slug);
  const adminChoropleth = useAdminRegions(slug, adminLevel);
  const adminDistricts = useAdminRegions(slug, 2); // stable basis for KPIs
  const hazards = useHazardLayers(slug);
  const shelters = useShelters(slug);
  const incidents = useIncidents(slug);
  const roads = useRoads(slug);
  const rivers = useRivers(slug);

  const flood = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: (hazards.data?.features ?? []).filter(
        (f) => f.properties.layer_type === "flood_extent",
      ),
    }),
    [hazards.data],
  );
  const landslide = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: (hazards.data?.features ?? []).filter(
        (f) => f.properties.layer_type === "landslide_susceptibility",
      ),
    }),
    [hazards.data],
  );

  const mapData: MapData = {
    admin: adminChoropleth.data,
    flood,
    landslide,
    roads: roads.data,
    shelters: shelters.data,
    incidents: incidents.data,
    rivers: rivers.data,
  };

  const counts: Partial<Record<LayerKey, number | undefined>> = {
    admin: adminChoropleth.data?.features.length,
    flood: flood.features.length,
    landslide: landslide.features.length,
    roads: roads.data?.features.length,
    shelters: shelters.data?.features.length,
    incidents: incidents.data?.features.length,
    rivers: rivers.data?.features.length,
  };

  const kpis = useMemo(
    () =>
      computeKpis({
        adminLevel2: adminDistricts.data,
        incidents: incidents.data,
        shelters: shelters.data,
        roads: roads.data,
      }),
    [adminDistricts.data, incidents.data, shelters.data, roads.data],
  );

  const bbox = useMemo<[number, number, number, number] | null>(() => {
    const b = detail.data?.bbox;
    return b ? [b.min_lon, b.min_lat, b.max_lon, b.max_lat] : null;
  }, [detail.data]);

  const kpisLoading = adminDistricts.isLoading || incidents.isLoading || roads.isLoading;

  const [leftOpen, setLeftOpen] = useState(true);
  // Context panel starts closed so the map gets full width; it opens on select.
  const [rightOpen, setRightOpen] = useState(false);
  // Open the context panel automatically when a feature is selected.
  useEffect(() => {
    if (selected) setRightOpen(true);
  }, [selected]);

  if (!slug) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        {t("sense.noScenario")}
      </div>
    );
  }

  if (detail.isError) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
        <AlertTriangle className="h-8 w-8 text-signal-crit" />
        <p className="text-sm text-muted-foreground">{t("sense.loadError")}</p>
        <Button variant="secondary" onClick={() => detail.refetch()}>
          {t("common.retry")}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3 p-3">
      <KpiStrip kpis={kpis} isLoading={kpisLoading} />

      <div className="flex min-h-0 flex-1 gap-3">
        {leftOpen && (
          <aside className="hidden w-72 shrink-0 overflow-hidden rounded-lg border border-border bg-surface md:block">
            <LayerPanel
              visibility={visibility}
              counts={counts}
              onToggle={toggleLayer}
              adminLevel={adminLevel}
              onAdminLevel={setAdminLevel}
              sources={detail.data?.sources ?? []}
            />
          </aside>
        )}

        <div className="relative min-w-0 flex-1 overflow-hidden rounded-lg border border-border">
          <MapCanvas
            key={theme}
            theme={theme}
            bbox={bbox}
            visibility={visibility}
            data={mapData}
            selected={selected}
            onSelect={select}
            onClearSelection={clearSelection}
          />

          {/* Collapse/expand toggles (desktop). */}
          <button
            type="button"
            onClick={() => setLeftOpen((v) => !v)}
            aria-label={t("sense.toggleLayers")}
            className="absolute left-3 top-3 z-10 hidden items-center gap-1.5 rounded-md border border-border bg-surface/90 px-2.5 py-1.5 text-2xs font-medium text-foreground shadow-e2 backdrop-blur transition-colors hover:bg-accent md:flex"
          >
            <Layers3 className="h-3.5 w-3.5" />
            {leftOpen ? t("sense.hidePanel") : t("sense.showLayers")}
          </button>
          {!rightOpen && (
            <button
              type="button"
              onClick={() => setRightOpen(true)}
              aria-label={t("sense.toggleDetails")}
              className="absolute right-3 top-3 z-10 hidden items-center gap-1.5 rounded-md border border-border bg-surface/90 px-2.5 py-1.5 text-2xs font-medium text-foreground shadow-e2 backdrop-blur transition-colors hover:bg-accent lg:flex"
            >
              <PanelRightOpen className="h-3.5 w-3.5" />
              {t("sense.showDetails")}
            </button>
          )}
        </div>

        {rightOpen && (
          <aside
            className={cn(
              "w-80 shrink-0 overflow-hidden rounded-lg border border-border bg-surface",
              "hidden lg:block",
            )}
          >
            <ContextPanel
              selected={selected}
              slug={slug}
              onClose={() => {
                clearSelection();
                setRightOpen(false);
              }}
            />
          </aside>
        )}
      </div>
    </div>
  );
}
