import { AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Separator } from "@/components/ui/separator";
import { ProvenanceBadge } from "@/features/decide/scorecard/ProvenanceBadge";
import type { ScoreResult, SubMetric } from "@/lib/api";
import { cn } from "@/lib/utils";

const pct = (score: number) => `${Math.round(score * 100)}%`;

function humanize(key: string): string {
  return key.replace(/_/g, " ");
}

function RawNumbers({ raw }: { raw: SubMetric["raw"] }) {
  return (
    <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-0.5 font-mono text-2xs text-muted-foreground">
      {Object.entries(raw).map(([k, v]) => (
        <div key={k} className="flex justify-between gap-2">
          <dt className="truncate">{humanize(k)}</dt>
          <dd className="text-foreground">{typeof v === "number" ? v.toLocaleString() : v}</dd>
        </div>
      ))}
    </dl>
  );
}

function MetricRow({ metric }: { metric: SubMetric }) {
  const { t } = useTranslation();
  return (
    <div className="py-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">
            {t(`decide.metric.${metric.key}`)}
          </span>
          <ProvenanceBadge provenance={metric.provenance} />
        </div>
        <span className="font-mono text-sm font-semibold tabular-nums text-foreground">
          {pct(metric.score)}
        </span>
      </div>
      <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn(
            "h-full rounded-full",
            metric.provenance === "synthetic"
              ? "bg-signal-warn"
              : metric.provenance === "assumption"
                ? "bg-signal-info"
                : "bg-primary",
          )}
          style={{ width: `${Math.round(metric.score * 100)}%` }}
        />
      </div>
      <div className="mt-1 text-2xs text-muted-foreground">
        {t("decide.weightLabel", { weight: Math.round(metric.weight * 100) })}
      </div>
      <RawNumbers raw={metric.raw} />
      {metric.notes.map((n) => (
        <p key={n} className="mt-1 text-2xs italic text-muted-foreground">
          {n}
        </p>
      ))}
    </div>
  );
}

export function Scorecard({ result }: { result: ScoreResult }) {
  const { t } = useTranslation();
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
          {t("decide.overall")}
        </span>
        <span className="font-mono text-3xl font-semibold tabular-nums text-foreground">
          {result.overall.toFixed(1)}
          <span className="ml-1 text-sm text-muted-foreground">/ 100</span>
        </span>
      </div>

      {result.uses_synthetic_data && (
        <div className="mt-2 flex items-start gap-2 rounded-md border border-signal-warn/30 bg-signal-warn/10 px-2.5 py-1.5 text-2xs text-signal-warn">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>{t("decide.syntheticBanner")}</span>
        </div>
      )}

      <Separator className="my-2" />
      <div className="divide-y divide-border">
        {result.metrics.map((m) => (
          <MetricRow key={m.key} metric={m} />
        ))}
      </div>

      {result.coverage_gaps.length > 0 && (
        <>
          <Separator className="my-2" />
          <div>
            <h4 className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-foreground">
              <AlertTriangle className="h-4 w-4 text-signal-crit" />
              {t("decide.coverageGaps")}
            </h4>
            <p className="mb-2 text-2xs text-muted-foreground">{t("decide.coverageGapsHint")}</p>
            <ul className="flex flex-col gap-1">
              {result.coverage_gaps.slice(0, 6).map((g) => (
                <li key={g.pcode} className="flex justify-between text-2xs">
                  <span className="text-foreground">{g.name}</span>
                  <span className="font-mono text-muted-foreground">
                    {g.at_risk_population.toLocaleString()} {t("decide.atRiskShort")}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      <Separator className="my-2" />
      <details className="text-2xs text-muted-foreground">
        <summary className="cursor-pointer select-none font-medium">
          {t("decide.assumptions")}
        </summary>
        <ul className="mt-1 list-disc pl-4">
          {result.assumptions_used.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}
