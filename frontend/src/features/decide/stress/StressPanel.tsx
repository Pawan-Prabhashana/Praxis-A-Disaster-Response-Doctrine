import { AlertTriangle, Dices, Info, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useStressRuns, useStressTest, useUncertaintyDefaults } from "@/features/decide/hooks";
import { ParamClassBadge } from "@/features/decide/stress/ParamClassBadge";
import { StressHistogram } from "@/features/decide/stress/StressHistogram";
import type { StressResult, UncertaintyConfig } from "@/lib/api";

interface StressPanelProps {
  slug: string;
  playbookId: number | null;
}

export function StressPanel({ slug, playbookId }: StressPanelProps) {
  const { t } = useTranslation();
  const defaults = useUncertaintyDefaults(slug);
  const runs = useStressRuns(slug, playbookId);
  const stress = useStressTest(slug);

  const [config, setConfig] = useState<UncertaintyConfig | null>(null);
  const [nIterations, setNIterations] = useState(500);

  // Seed the editable config from the server defaults once loaded.
  useEffect(() => {
    if (defaults.data && !config) setConfig(structuredClone(defaults.data));
  }, [defaults.data, config]);

  if (playbookId == null) {
    return <p className="text-sm text-muted-foreground">{t("decide.stress.saveFirst")}</p>;
  }
  if (!config) return <Skeleton className="h-64 w-full" />;

  const toggleParam = (key: string) =>
    setConfig({
      ...config,
      params: config.params.map((p) => (p.key === key ? { ...p, enabled: !p.enabled } : p)),
    });

  const result: StressResult | undefined = stress.data?.result ?? runs.data?.[0]?.result;

  const run = () => stress.mutate({ id: playbookId, body: { config, n_iterations: nIterations } });

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start gap-2 rounded-md border border-signal-info/30 bg-signal-info/10 px-2.5 py-1.5 text-2xs text-signal-info">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>{t("decide.stress.epistemic")}</span>
      </div>

      {/* Config */}
      <div>
        <div className="mb-2 flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-2xs text-muted-foreground">
            {t("decide.stress.iterationsLabel")}
            <input
              type="number"
              min={50}
              max={5000}
              step={50}
              value={nIterations}
              onChange={(e) => setNIterations(Math.max(50, Math.min(5000, Number(e.target.value))))}
              className="w-20 rounded-md border border-input bg-surface-raised px-2 py-1 font-mono text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>
          <label className="flex items-center gap-1.5 text-2xs text-muted-foreground">
            {t("decide.stress.targetLabel")}
            <input
              type="number"
              min={0}
              max={100}
              value={config.target_score}
              onChange={(e) =>
                setConfig({
                  ...config,
                  target_score: Math.max(0, Math.min(100, Number(e.target.value))),
                })
              }
              className="w-16 rounded-md border border-input bg-surface-raised px-2 py-1 font-mono text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>
        </div>

        <ul className="flex flex-col gap-1.5">
          {config.params.map((p) => (
            <li key={p.key} className="rounded-md border border-border bg-surface-raised p-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={p.enabled}
                  onChange={() => toggleParam(p.key)}
                  aria-label={p.label}
                  className="h-4 w-4 shrink-0 accent-[hsl(var(--primary))]"
                />
                <span className="flex-1 text-sm text-foreground">{p.label}</span>
                <ParamClassBadge paramClass={p.param_class} />
              </div>
              <div className="ml-6 mt-0.5 font-mono text-2xs text-muted-foreground">
                {p.distribution.kind === "triangular"
                  ? `triangular(min ${p.distribution.low}, mode ${p.distribution.mode}, max ${p.distribution.high})`
                  : p.distribution.kind}
              </div>
              <details className="ml-6 mt-0.5 text-2xs text-muted-foreground">
                <summary className="cursor-pointer select-none">{t("decide.stress.basis")}</summary>
                <p className="mt-0.5">{p.basis}</p>
              </details>
            </li>
          ))}
        </ul>

        <Button className="mt-3 w-full" onClick={run} disabled={stress.isPending}>
          {stress.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Dices className="h-4 w-4" />
          )}
          {t("decide.stress.run")}
        </Button>
        {stress.isError && (
          <p className="mt-1 text-2xs text-signal-crit">{t("decide.stress.error")}</p>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          <Separator />
          <StressResultView result={result} />
        </>
      )}
    </div>
  );
}

function StressResultView({ result }: { result: StressResult }) {
  const { t } = useTranslation();
  const o = result.overall;
  const r = result.robustness;
  const reversal = result.point_overall - o.median;
  return (
    <div>
      <p className="mb-2 text-sm text-surface-foreground">
        {t("decide.stress.statement", {
          low: Math.round(o.p05),
          high: Math.round(o.p95),
          median: Math.round(o.median),
          worst: Math.round(r.worst_plausible),
        })}
      </p>
      <StressHistogram summary={o} point={result.point_overall} target={r.target_score} />
      <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-2xs">
        <span className="text-muted-foreground">{t("decide.stress.worstPlausible")}</span>
        <span className="text-right text-signal-crit">{r.worst_plausible.toFixed(1)}</span>
        <span className="text-muted-foreground">{t("decide.stress.median")}</span>
        <span className="text-right text-foreground">{o.median.toFixed(1)}</span>
        <span className="text-muted-foreground">{t("decide.stress.point")}</span>
        <span className="text-right text-foreground">{result.point_overall.toFixed(1)}</span>
        <span className="text-muted-foreground">
          {t("decide.stress.meetsTarget", { target: Math.round(r.target_score) })}
        </span>
        <span className="text-right text-foreground">
          {Math.round(r.probability_meets_target * 100)}%
        </span>
      </div>
      {Math.abs(reversal) >= 3 && (
        <div className="mt-2 flex items-start gap-1.5 text-2xs text-signal-warn">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            {reversal > 0
              ? t("decide.stress.optimistic", { delta: Math.round(reversal) })
              : t("decide.stress.pessimistic", { delta: Math.round(-reversal) })}
          </span>
        </div>
      )}
      <p className="mt-2 text-2xs text-muted-foreground">
        {t("decide.stress.runMeta", { n: result.n_iterations, seed: result.seed })}
      </p>
    </div>
  );
}
