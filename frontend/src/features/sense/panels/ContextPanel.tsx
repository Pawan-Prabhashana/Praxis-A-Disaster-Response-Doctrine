import { MousePointerClick, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useDischarge } from "@/features/sense/hooks";
import { DischargeChart } from "@/features/sense/panels/DischargeChart";
import type { SelectedFeature } from "@/features/sense/store";
import { cn } from "@/lib/utils";

interface ContextPanelProps {
  selected: SelectedFeature | null;
  slug: string | null;
  onClose: () => void;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3 py-1 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium text-foreground">{value}</span>
    </div>
  );
}

function ProvenanceLine({ source, synthetic }: { source: string; synthetic: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="mt-3 flex items-center gap-2 text-2xs text-muted-foreground">
      <span className={cn("h-2 w-2 rounded-full", synthetic ? "bg-signal-warn" : "bg-signal-ok")} />
      {synthetic ? t("sense.provenance.sample") : t("sense.provenance.real")} · {source}
    </div>
  );
}

function RiverDetail({ selected, slug }: { selected: SelectedFeature; slug: string | null }) {
  const { t } = useTranslation();
  if (selected.kind !== "river") return null;
  const { data, isLoading, isError } = useDischarge(slug, selected.props.id);
  const point = data?.points.find((p) => p.river_point_id === selected.props.id) ?? data?.points[0];

  return (
    <div>
      <Row label={t("sense.detail.river")} value={selected.props.river_name ?? "—"} />
      <Row label={t("sense.detail.station")} value={selected.props.name} />
      <Separator className="my-3" />
      <div className="mb-2 text-2xs font-medium uppercase tracking-wider text-muted-foreground">
        {t("sense.detail.discharge")}
      </div>
      {isLoading && <Skeleton className="h-40 w-full" />}
      {isError && <p className="text-sm text-signal-crit">{t("sense.detail.dischargeError")}</p>}
      {point && <DischargeChart data={point} />}
      {point && <ProvenanceLine source={point.source} synthetic={point.is_synthetic} />}
    </div>
  );
}

export function ContextPanel({ selected, slug, onClose }: ContextPanelProps) {
  const { t } = useTranslation();

  if (!selected) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
        <MousePointerClick className="h-8 w-8 text-muted-foreground/60" aria-hidden />
        <p className="max-w-[16rem] text-sm text-muted-foreground">{t("sense.detail.empty")}</p>
      </div>
    );
  }

  const titles: Record<SelectedFeature["kind"], string> = {
    incident: t("sense.detail.titleIncident"),
    shelter: t("sense.detail.titleShelter"),
    river: t("sense.detail.titleRiver"),
    admin: t("sense.detail.titleAdmin"),
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">{titles[selected.kind]}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label={t("common.close")}
          className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <Separator />

      <div className="flex-1 overflow-y-auto p-4">
        {selected.kind === "incident" && (
          <>
            <div className="mb-2 flex items-center gap-2">
              <Badge variant="warn">{selected.props.type}</Badge>
              {selected.props.severity && (
                <Badge variant="outline">{selected.props.severity}</Badge>
              )}
            </div>
            {selected.props.description && (
              <p className="mb-3 text-sm text-surface-foreground">{selected.props.description}</p>
            )}
            <Row
              label={t("sense.detail.occurred")}
              value={selected.props.occurred_at?.slice(0, 10) ?? "—"}
            />
            <ProvenanceLine
              source={selected.props.source}
              synthetic={selected.props.is_synthetic}
            />
          </>
        )}

        {selected.kind === "shelter" && (
          <>
            <div className="mb-2 text-base font-semibold text-foreground">
              {selected.props.name}
            </div>
            <Row label={t("sense.detail.kind")} value={selected.props.kind.replace(/_/g, " ")} />
            <Row
              label={t("sense.detail.capacity")}
              value={
                selected.props.capacity != null
                  ? selected.props.capacity.toLocaleString()
                  : t("sense.detail.unknown")
              }
            />
            <ProvenanceLine
              source={t("sense.detail.candidateOsm")}
              synthetic={selected.props.is_synthetic}
            />
          </>
        )}

        {selected.kind === "admin" && (
          <>
            <div className="mb-2 text-base font-semibold text-foreground">
              {selected.props.name_en}
            </div>
            <Row label={t("sense.detail.pcode")} value={selected.props.pcode} />
            <Row
              label={t("sense.detail.population")}
              value={
                selected.props.population != null
                  ? selected.props.population.toLocaleString()
                  : t("sense.detail.unknown")
              }
            />
            <ProvenanceLine
              source={selected.props.source}
              synthetic={selected.props.is_synthetic}
            />
          </>
        )}

        {selected.kind === "river" && <RiverDetail selected={selected} slug={slug} />}
      </div>
    </div>
  );
}
