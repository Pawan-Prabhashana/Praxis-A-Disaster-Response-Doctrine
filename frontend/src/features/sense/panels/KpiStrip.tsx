import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { SenseKpis } from "@/features/sense/kpis";

interface KpiStripProps {
  kpis: SenseKpis | null;
  isLoading: boolean;
}

function KpiCard({
  label,
  value,
  sub,
  sample,
}: {
  label: string;
  value: string;
  sub?: string;
  sample?: boolean;
}) {
  return (
    <Card className="min-w-[9.5rem] flex-1 px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        {sample && <Badge variant="warn">sample</Badge>}
      </div>
      <div className="mt-1 font-mono text-2xl font-semibold tabular-nums text-foreground">
        {value}
      </div>
      {sub && <div className="mt-0.5 text-2xs text-muted-foreground">{sub}</div>}
    </Card>
  );
}

export function KpiStrip({ kpis, isLoading }: KpiStripProps) {
  const { t } = useTranslation();

  if (isLoading || !kpis) {
    return (
      <div className="flex gap-3 overflow-x-auto">
        {Array.from({ length: 5 }).map((_, i) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: fixed-length skeletons
          <Skeleton key={i} className="h-[4.75rem] min-w-[9.5rem] flex-1" />
        ))}
      </div>
    );
  }

  const nf = (n: number) => n.toLocaleString();
  const capacitySub =
    kpis.shelterCapacityCount > 0
      ? t("sense.kpi.capacitySub", {
          capacity: nf(kpis.shelterCapacityKnown),
          sites: nf(kpis.shelterCapacityCount),
        })
      : t("sense.kpi.capacityUnknown");

  return (
    <div className="flex gap-3 overflow-x-auto pb-1">
      <KpiCard label={t("sense.kpi.districts")} value={nf(kpis.districts)} />
      <KpiCard
        label={t("sense.kpi.population")}
        value={nf(kpis.population)}
        sub={t("sense.kpi.populationSub")}
      />
      <KpiCard
        label={t("sense.kpi.incidents")}
        value={nf(kpis.incidents)}
        sub={t("sense.kpi.incidentsSub")}
      />
      <KpiCard label={t("sense.kpi.shelters")} value={nf(kpis.shelters)} sub={capacitySub} />
      <KpiCard
        label={t("sense.kpi.roads")}
        value={`${nf(Math.round(kpis.roadsKm))} km`}
        sub={t("sense.kpi.roadsClosed", { km: nf(Math.round(kpis.closedRoadsKm)) })}
        sample
      />
    </div>
  );
}
