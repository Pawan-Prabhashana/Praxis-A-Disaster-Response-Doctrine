import { AlertTriangle, GitCompareArrows, Info, ShieldCheck, Target } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { LearnMap } from "@/features/learn/LearnMap";
import { RankScatter } from "@/features/learn/RankScatter";
import type { AfterAction, DistrictComparison, LessonSeverity } from "@/lib/api";
import { useUiStore } from "@/store/ui";

const num = (v: number) => Math.round(v).toLocaleString();

const SEVERITY_VARIANT: Record<LessonSeverity, "crit" | "warn" | "info"> = {
  crit: "crit",
  warn: "warn",
  info: "info",
};
const ALIGN_VARIANT: Record<string, "ok" | "warn" | "crit" | "info"> = {
  strong: "ok",
  moderate: "info",
  weak: "warn",
  inverted: "crit",
};

interface AfterActionViewProps {
  aa: AfterAction;
  bbox: [number, number, number, number] | null;
}

export function AfterActionView({ aa, bbox }: AfterActionViewProps) {
  const { t } = useTranslation();
  const theme = useUiStore((s) => s.theme);
  const { result, lessons } = aa;

  const impactByPcode = useMemo(
    () => Object.fromEntries(result.districts.map((d) => [d.pcode, d.impact_score])),
    [result.districts],
  );
  const priorityPcodes = useMemo(
    () => result.districts.filter((d) => d.is_priority).map((d) => d.pcode),
    [result.districts],
  );

  return (
    <div className="flex flex-col gap-4">
      {/* Framing — predicted vs recorded (mandatory honest framing). */}
      <div className="flex items-start gap-2 rounded-md border border-signal-info/30 bg-signal-info/10 px-3 py-2 text-2xs text-signal-info">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <span>{t("learn.framing", { year: result.event_year ?? "—" })}</span>
      </div>

      {/* Alignment headline. */}
      <AlignmentCallout aa={aa} />

      {/* Map + assessment. */}
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg border border-border" style={{ minHeight: 260 }}>
          <div className="h-64">
            <LearnMap
              slug={result.scenario_slug}
              theme={theme}
              bbox={bbox}
              impactByPcode={impactByPcode}
              priorityPcodes={priorityPcodes}
            />
          </div>
          <p className="border-t border-border px-3 py-1.5 text-2xs text-muted-foreground">
            {t("learn.mapCaption")}
          </p>
        </div>
        <div className="rounded-lg border border-border p-3">
          <div className="mb-1.5 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-signal-info" />
            <h3 className="text-sm font-semibold text-foreground">{t("learn.assessment")}</h3>
            <Badge variant="outline">
              {lessons.generator === "llm" ? t("learn.aiNarrated") : t("learn.template")}
            </Badge>
          </div>
          <p className="text-sm leading-relaxed text-surface-foreground">{lessons.assessment}</p>
        </div>
      </div>

      {/* Predicted vs recorded ranking scatter. */}
      <div className="rounded-lg border border-border p-3">
        <div className="mb-1 flex items-center gap-2">
          <GitCompareArrows className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-foreground">{t("learn.rankTitle")}</h3>
        </div>
        <p className="mb-2 text-2xs text-muted-foreground">{t("learn.rankHint")}</p>
        <RankScatter districts={result.districts} />
      </div>

      {/* Recorded impact table. */}
      <RecordedImpactTable districts={result.districts} year={result.event_year} />

      {/* Blind spots. */}
      {result.blind_spots.length > 0 && (
        <div className="rounded-lg border border-signal-crit/30 bg-signal-crit/5 p-3">
          <div className="mb-1.5 flex items-center gap-2">
            <Target className="h-4 w-4 text-signal-crit" />
            <h3 className="text-sm font-semibold text-foreground">{t("learn.blindSpots")}</h3>
          </div>
          <ul className="flex flex-col gap-1 text-2xs text-muted-foreground">
            {result.blind_spots.map((d) => (
              <li key={d.pcode}>
                <span className="font-medium text-foreground">{d.name}</span> —{" "}
                {t("learn.blindSpotDetail", {
                  deaths: num(d.deaths),
                  affected: num(d.affected),
                })}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Lessons. */}
      <div className="rounded-lg border border-border p-3">
        <h3 className="mb-2 text-sm font-semibold text-foreground">{t("learn.lessons")}</h3>
        <ul className="flex flex-col gap-2">
          {lessons.lessons.map((lesson) => (
            <li
              key={lesson.key}
              className="flex items-start gap-2 rounded-md border border-border bg-surface-raised p-2.5"
            >
              {lesson.severity === "crit" ? (
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-signal-crit" />
              ) : (
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              )}
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">{lesson.title}</span>
                  <Badge variant={SEVERITY_VARIANT[lesson.severity]}>{lesson.severity}</Badge>
                </div>
                <p className="mt-0.5 text-2xs text-muted-foreground">{lesson.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <p className="text-2xs text-muted-foreground">
        {t("learn.provenanceFooter", {
          generator: lessons.generator === "llm" ? t("learn.aiNarrated") : t("learn.template"),
        })}
      </p>
    </div>
  );
}

function AlignmentCallout({ aa }: { aa: AfterAction }) {
  const { t } = useTranslation();
  const a = aa.result.alignment;
  const variant = ALIGN_VARIANT[a.label] ?? "info";
  return (
    <div className="rounded-lg border border-border bg-surface-raised p-3">
      <div className="mb-1 flex items-center gap-2">
        <h3 className="text-sm font-semibold text-foreground">{t("learn.alignmentTitle")}</h3>
        <Badge variant={variant}>{t(`learn.alignLabel.${a.label}`)}</Badge>
      </div>
      <p className="text-sm text-surface-foreground">
        {t("learn.alignmentSummary", {
          rho: a.spearman,
          overlap: a.top_k_overlap,
          k: a.top_k,
          n: a.n_with_data,
        })}
      </p>
    </div>
  );
}

function RecordedImpactTable({
  districts,
  year,
}: {
  districts: DistrictComparison[];
  year: number | null;
}) {
  const { t } = useTranslation();
  const rows = [...districts].sort((a, b) => a.impact_rank - b.impact_rank);
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="flex items-center gap-2 border-b border-border bg-surface-raised px-3 py-2">
        <h3 className="text-sm font-semibold text-foreground">
          {t("learn.recordedTitle", { year: year ?? "—" })}
        </h3>
        <Badge variant="ok">{t("learn.realBadge")}</Badge>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-2xs">
          <thead className="text-muted-foreground">
            <tr>
              <th className="px-3 py-1.5 font-medium">{t("learn.colDistrict")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("learn.colPredRank")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("learn.colDeaths")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("learn.colAffected")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("learn.colHouses")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("learn.colImpact")}</th>
              <th className="px-3 py-1.5 text-right font-medium">{t("learn.colImpactRank")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((d) => (
              <tr key={d.pcode} className="border-t border-border">
                <td className="px-3 py-1.5">
                  <span className="text-foreground">{d.name}</span>
                  {d.under_prioritised && (
                    <span className="ml-1.5 text-signal-crit">{t("learn.underTag")}</span>
                  )}
                  {!d.is_priority && (
                    <span className="ml-1.5 text-muted-foreground">
                      {t("learn.notPriorityTag")}
                    </span>
                  )}
                </td>
                <td className="px-3 py-1.5 text-right font-mono text-muted-foreground">
                  #{d.predicted_rank}
                </td>
                {d.has_data ? (
                  <>
                    <td className="px-3 py-1.5 text-right font-mono text-foreground">
                      {num(d.deaths)}
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono text-foreground">
                      {num(d.affected)}
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono text-foreground">
                      {num(d.houses_destroyed)}
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono text-foreground">
                      {d.impact_score.toFixed(1)}
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono text-foreground">
                      #{d.impact_rank}
                    </td>
                  </>
                ) : (
                  <td className="px-3 py-1.5 text-muted-foreground" colSpan={5}>
                    {t("learn.noData")}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
