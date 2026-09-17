import { useQueries } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useTranslation } from "react-i18next";

import { BandBar } from "@/features/decide/stress/BandBar";
import { type StressEntry, analyseWinners } from "@/features/decide/stress/logic";
import { api } from "@/lib/api";
import type { Playbook, StressRun } from "@/lib/api";
import { cn } from "@/lib/utils";

const COLORS = ["hsl(var(--primary))", "hsl(var(--signal-info))", "hsl(var(--signal-ok))"];

interface CompareUncertaintyProps {
  slug: string;
  playbooks: Playbook[];
}

export function CompareUncertainty({ slug, playbooks }: CompareUncertaintyProps) {
  const { t } = useTranslation();

  const runQueries = useQueries({
    queries: playbooks.map((pb) => ({
      queryKey: ["stress-runs", slug, pb.id],
      queryFn: () => api.listStressRuns(slug, pb.id),
      staleTime: 5 * 60_000,
    })),
  });

  const withRuns = playbooks
    .map((pb, i) => ({ pb, latest: runQueries[i]?.data?.[0] as StressRun | undefined }))
    .filter((x): x is { pb: Playbook; latest: StressRun } => !!x.latest);

  if (withRuns.length < 2) {
    return (
      <div className="rounded-lg border border-dashed border-border p-4 text-center text-2xs text-muted-foreground">
        {t("decide.stress.compareHint")}
      </div>
    );
  }

  const target = withRuns[0]?.latest.result.robustness.target_score ?? 60;
  const entries: StressEntry[] = withRuns.map(({ pb, latest }) => ({
    id: pb.id,
    name: pb.name,
    point: latest.result.point_overall,
    median: latest.result.overall.median,
    p05: latest.result.overall.p05,
    p95: latest.result.overall.p95,
  }));
  const { reversal, robustWinnerId, pointWinnerId } = analyseWinners(entries);
  const robustName = entries.find((e) => e.id === robustWinnerId)?.name ?? "";
  const pointName = entries.find((e) => e.id === pointWinnerId)?.name ?? "";

  return (
    <div>
      <h4 className="mb-1 text-sm font-medium text-foreground">
        {t("decide.stress.underUncertainty")}
      </h4>
      <p className="mb-3 text-2xs text-muted-foreground">{t("decide.stress.epistemicShort")}</p>

      {reversal && (
        <div className="mb-3 flex items-start gap-2 rounded-md border border-signal-warn/40 bg-signal-warn/10 px-3 py-2 text-xs text-signal-warn">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{t("decide.stress.reversal", { robust: robustName, point: pointName })}</span>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {withRuns.map(({ pb, latest }, i) => {
          const o = latest.result.overall;
          const r = latest.result.robustness;
          const isRobustWinner = pb.id === robustWinnerId;
          return (
            <div key={pb.id}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="flex items-center gap-1.5 truncate text-xs font-medium text-foreground">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-sm"
                    style={{ background: COLORS[i % COLORS.length] }}
                  />
                  {pb.name}
                  {isRobustWinner && (
                    <span className="rounded bg-signal-ok/15 px-1.5 py-0.5 text-2xs text-signal-ok">
                      {t("decide.stress.mostRobust")}
                    </span>
                  )}
                </span>
                <span className="shrink-0 font-mono text-2xs text-muted-foreground">
                  {t("decide.stress.worstShort")}{" "}
                  <span
                    className={cn(
                      "font-semibold",
                      isRobustWinner ? "text-signal-ok" : "text-foreground",
                    )}
                  >
                    {r.worst_plausible.toFixed(0)}
                  </span>{" "}
                  · med {o.median.toFixed(0)} · {Math.round(r.probability_meets_target * 100)}%≥
                  {Math.round(r.target_score)}
                </span>
              </div>
              <BandBar
                p05={o.p05}
                median={o.median}
                p95={o.p95}
                point={latest.result.point_overall}
                color={COLORS[i % COLORS.length] ?? "hsl(var(--primary))"}
                target={target}
              />
            </div>
          );
        })}
      </div>
      <p className="mt-2 text-2xs text-muted-foreground">{t("decide.stress.bandLegend")}</p>
    </div>
  );
}
