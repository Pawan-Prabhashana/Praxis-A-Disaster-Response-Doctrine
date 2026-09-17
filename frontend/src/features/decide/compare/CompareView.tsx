import { Trophy } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Skeleton } from "@/components/ui/skeleton";
import { CompareChart } from "@/features/decide/compare/CompareChart";
import { CompareUncertainty } from "@/features/decide/compare/CompareUncertainty";
import { bestInRow } from "@/features/decide/compare/logic";
import { usePlaybooks } from "@/features/decide/hooks";
import { ProvenanceBadge } from "@/features/decide/scorecard/ProvenanceBadge";
import { useDecideStore } from "@/features/decide/store";
import type { Playbook, Provenance } from "@/lib/api";
import { cn } from "@/lib/utils";

const METRIC_KEYS = [
  "population_coverage",
  "shelter_adequacy",
  "accessibility",
  "resource_adequacy",
];

function metricValue(pb: Playbook, key: string): number {
  return pb.score_result?.metrics.find((m) => m.key === key)?.score ?? 0;
}

function metricProvenance(playbooks: Playbook[], key: string): Provenance {
  for (const pb of playbooks) {
    const m = pb.score_result?.metrics.find((x) => x.key === key);
    if (m) return m.provenance;
  }
  return "real";
}

export function CompareView({ slug }: { slug: string }) {
  const { t } = useTranslation();
  const playbooks = usePlaybooks(slug);
  const compareIds = useDecideStore((s) => s.compareIds);

  if (playbooks.isLoading) return <Skeleton className="h-96 w-full" />;

  const selected = (playbooks.data ?? []).filter(
    (pb) => compareIds.includes(pb.id) && pb.score_result,
  );

  if (selected.length < 2) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-8 text-center">
        <Trophy className="h-8 w-8 text-muted-foreground/60" />
        <p className="max-w-sm text-sm text-muted-foreground">{t("decide.compareHint")}</p>
      </div>
    );
  }

  const cols = `minmax(11rem,1.4fr) ${selected.map(() => "1fr").join(" ")}`;
  const overallValues = selected.map((pb) => pb.score_result?.overall ?? 0);
  const overallBest = bestInRow(overallValues);

  return (
    <div className="flex h-full min-h-0 flex-col gap-4 overflow-y-auto rounded-lg border border-border bg-surface p-4">
      <CompareChart playbooks={selected} />

      <div className="overflow-x-auto">
        <div className="min-w-[36rem]">
          {/* Header */}
          <div
            className="grid items-end gap-2 border-b border-border pb-2"
            style={{ gridTemplateColumns: cols }}
          >
            <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
              {t("decide.metricCol")}
            </span>
            {selected.map((pb) => (
              <span key={pb.id} className="truncate text-sm font-semibold text-foreground">
                {pb.name}
              </span>
            ))}
          </div>

          {/* Overall */}
          <div
            className="grid items-center gap-2 border-b border-border py-2.5"
            style={{ gridTemplateColumns: cols }}
          >
            <span className="text-sm font-semibold text-foreground">{t("decide.overall")}</span>
            {selected.map((pb, i) => {
              const v = overallValues[i] ?? 0;
              const best = overallBest[i];
              return (
                <span
                  key={pb.id}
                  className={cn(
                    "flex items-center gap-1 font-mono text-lg font-semibold tabular-nums",
                    best ? "text-primary" : "text-foreground",
                  )}
                >
                  {best && <Trophy className="h-3.5 w-3.5" />}
                  {v.toFixed(1)}
                </span>
              );
            })}
          </div>

          {/* Metric rows */}
          {METRIC_KEYS.map((key) => {
            const values = selected.map((pb) => metricValue(pb, key));
            const bestFlags = bestInRow(values);
            return (
              <div
                key={key}
                className="grid items-center gap-2 border-b border-border py-2"
                style={{ gridTemplateColumns: cols }}
              >
                <span className="flex items-center gap-1.5">
                  <span className="text-sm text-foreground">{t(`decide.metric.${key}`)}</span>
                  <ProvenanceBadge provenance={metricProvenance(selected, key)} />
                </span>
                {selected.map((pb, i) => {
                  const v = values[i] ?? 0;
                  const isBest = bestFlags[i];
                  return (
                    <span
                      key={pb.id}
                      className={cn(
                        "font-mono text-sm tabular-nums",
                        isBest ? "font-semibold text-primary" : "text-muted-foreground",
                      )}
                    >
                      {Math.round(v * 100)}%
                    </span>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparison under modeled uncertainty (bands + robustness + reversal) */}
      <CompareUncertainty slug={slug} playbooks={selected} />

      {/* Coverage gaps per strategy */}
      <div>
        <h4 className="mb-2 text-sm font-medium text-foreground">{t("decide.coverageGaps")}</h4>
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: `repeat(${selected.length}, 1fr)` }}
        >
          {selected.map((pb) => (
            <div key={pb.id} className="rounded-md border border-border bg-surface-raised p-2.5">
              <div className="mb-1 truncate text-2xs font-semibold text-foreground">{pb.name}</div>
              {pb.score_result && pb.score_result.coverage_gaps.length > 0 ? (
                <ul className="flex flex-col gap-0.5">
                  {pb.score_result.coverage_gaps.slice(0, 4).map((g) => (
                    <li
                      key={g.pcode}
                      className="flex justify-between text-2xs text-muted-foreground"
                    >
                      <span>{g.name}</span>
                      <span className="font-mono">{g.at_risk_population.toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-2xs text-signal-ok">{t("decide.noGaps")}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
