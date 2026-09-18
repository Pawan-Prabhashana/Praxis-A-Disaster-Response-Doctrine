import { AlertTriangle, Info, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { ProvenanceBadge } from "@/features/decide/scorecard/ProvenanceBadge";
import { BandBar } from "@/features/decide/stress/BandBar";
import type { Brief, BriefSection } from "@/lib/api";

const num = (v: number) => Math.round(v).toLocaleString();
const score = (v: number) => v.toFixed(1);

/**
 * The rendered operational brief: an authoritative document whose numbers are
 * computed by Praxis (and validated by the numeric guard) with only the prose
 * structure AI-assisted. Honesty flags and the epistemic framing are preserved.
 */
export function BriefDocument({ brief }: { brief: Brief }) {
  const { t } = useTranslation();
  const { facts, content, guard } = brief;

  return (
    <article className="mx-auto flex max-w-3xl flex-col gap-4">
      <header>
        <h1 className="text-xl font-semibold text-foreground">{content.headline}</h1>
        <p className="mt-1 text-xs text-muted-foreground">
          {facts.scenario.name} &middot; {facts.scenario.hazard_type}
          {facts.scenario.event_date ? ` · ${facts.scenario.event_date}` : ""} &middot;{" "}
          {t("act.preparedAt", { date: new Date(brief.created_at).toLocaleString() })}
        </p>
      </header>

      <HonestyBanner brief={brief} />

      {content.sections.map((section) => (
        <SectionBlock
          key={section.key}
          section={section}
          brief={brief}
          aiNarrated={content.generator === "llm"}
        />
      ))}

      <footer className="border-t border-border pt-3 text-2xs text-muted-foreground">
        <p>
          {t("act.footerGenerated", {
            generator:
              content.generator === "llm" ? t("act.generatorLlm") : t("act.generatorTemplate"),
          })}
          {brief.model ? ` · ${brief.model}` : ""}
          {guard.repaired_sections.length > 0
            ? ` · ${t("act.guardRepaired", { count: guard.repaired_sections.length })}`
            : ""}
        </p>
      </footer>
    </article>
  );
}

function HonestyBanner({ brief }: { brief: Brief }) {
  const { t } = useTranslation();
  const ai = brief.content.generator === "llm";
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-start gap-2 rounded-md border border-signal-info/30 bg-signal-info/10 px-3 py-2 text-2xs text-signal-info">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{ai ? t("act.validatedNote") : t("act.templateNote")}</span>
      </div>
      {brief.facts.uses_synthetic_data && (
        <div className="flex items-start gap-2 rounded-md border border-signal-warn/30 bg-signal-warn/10 px-3 py-2 text-2xs text-signal-warn">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{t("act.syntheticWarn")}</span>
        </div>
      )}
      {brief.facts.robustness && (
        <div className="flex items-start gap-2 rounded-md border border-border bg-surface-raised px-3 py-2 text-2xs text-muted-foreground">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{brief.facts.robustness.epistemic_note}</span>
        </div>
      )}
    </div>
  );
}

function SectionBlock({
  section,
  brief,
  aiNarrated,
}: {
  section: BriefSection;
  brief: Brief;
  aiNarrated: boolean;
}) {
  const { t } = useTranslation();
  return (
    <section>
      <div className="mb-1 flex items-center gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">
          {section.title}
        </h2>
        {aiNarrated && section.from_template && (
          <Badge variant="outline">{t("act.verifiedTemplate")}</Badge>
        )}
      </div>
      {section.paragraphs.map((p, i) => (
        <p
          key={`${section.key}-${i}`}
          className="mb-2 text-sm leading-relaxed text-surface-foreground"
        >
          {p}
        </p>
      ))}
      {section.key === "performance" && <PerformanceExtras brief={brief} />}
    </section>
  );
}

function PerformanceExtras({ brief }: { brief: Brief }) {
  const { t } = useTranslation();
  const { scorecard, robustness } = brief.facts;
  return (
    <div className="mt-2 flex flex-col gap-3">
      <div className="overflow-hidden rounded-md border border-border">
        <table className="w-full text-left text-2xs">
          <thead className="bg-surface-raised text-muted-foreground">
            <tr>
              <th className="px-3 py-1.5 font-medium">{t("act.metric")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("act.scoreCol")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("act.weightCol")}</th>
              <th className="px-3 py-1.5 font-medium">{t("act.basisCol")}</th>
            </tr>
          </thead>
          <tbody>
            {scorecard.metrics.map((m) => (
              <tr key={m.key} className="border-t border-border">
                <td className="px-3 py-1.5 text-foreground">{m.label}</td>
                <td className="px-3 py-1.5 text-right font-mono text-foreground">
                  {score(m.score)}
                </td>
                <td className="px-3 py-1.5 text-right font-mono text-muted-foreground">
                  {m.weight_pct}%
                </td>
                <td className="px-3 py-1.5">
                  <ProvenanceBadge provenance={m.provenance} />
                </td>
              </tr>
            ))}
            <tr className="border-t border-border bg-surface-raised">
              <td className="px-3 py-1.5 font-semibold text-foreground">{t("act.overall")}</td>
              <td className="px-3 py-1.5 text-right font-mono font-semibold text-foreground">
                {score(scorecard.overall)}
              </td>
              <td />
              <td />
            </tr>
          </tbody>
        </table>
      </div>

      {robustness && (
        <div className="rounded-md border border-border p-3">
          <p className="mb-1.5 text-2xs font-medium text-foreground">{t("act.robustnessTitle")}</p>
          <BandBar
            p05={robustness.p05}
            median={robustness.median}
            p95={robustness.p95}
            point={robustness.point_overall}
            color="hsl(var(--signal-info))"
            target={robustness.target_score}
          />
          <p className="mt-1.5 font-mono text-2xs text-muted-foreground">
            {t("act.robustnessLine", {
              low: score(robustness.p05),
              high: score(robustness.p95),
              median: score(robustness.median),
              worst: score(robustness.worst_plausible),
              prob: robustness.probability_meets_target_pct,
              target: robustness.target_score,
            })}
          </p>
          <p className="mt-1 text-2xs text-muted-foreground">
            {t("act.reproFrom", { seed: robustness.seed, n: num(robustness.n_iterations) })}
          </p>
        </div>
      )}
    </div>
  );
}
