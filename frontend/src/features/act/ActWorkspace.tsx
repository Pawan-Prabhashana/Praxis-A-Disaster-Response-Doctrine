import { Dices, Download, FileText, Loader2, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BriefDocument } from "@/features/act/BriefDocument";
import { useBriefs, useCreateBrief } from "@/features/act/hooks";
import { usePlaybooks, useStressRuns } from "@/features/decide/hooks";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";
import { useQuery } from "@tanstack/react-query";

export function ActWorkspace() {
  const { t } = useTranslation();
  const slug = useUiStore((s) => s.selectedScenarioSlug);

  const playbooks = usePlaybooks(slug);
  const [playbookId, setPlaybookId] = useState<number | null>(null);
  const [stressRunId, setStressRunId] = useState<number | null>(null);
  const [activeBriefId, setActiveBriefId] = useState<number | null>(null);

  // Default to the first saved playbook once loaded.
  useEffect(() => {
    if (playbookId == null && playbooks.data && playbooks.data.length > 0) {
      setPlaybookId(playbooks.data[0]?.id ?? null);
    }
  }, [playbooks.data, playbookId]);

  const runs = useStressRuns(slug, playbookId);
  const briefs = useBriefs(slug, playbookId);
  const create = useCreateBrief(slug ?? "");

  // Default the attached stress run to the most recent one.
  useEffect(() => {
    setStressRunId(runs.data && runs.data.length > 0 ? (runs.data[0]?.id ?? null) : null);
  }, [runs.data]);

  // Show the newest existing brief for the selected playbook until one is generated.
  useEffect(() => {
    setActiveBriefId(briefs.data && briefs.data.length > 0 ? (briefs.data[0]?.id ?? null) : null);
  }, [briefs.data]);

  const briefQuery = useQuery({
    queryKey: ["brief", slug, playbookId, activeBriefId],
    queryFn: () => api.getBrief(slug as string, playbookId as number, activeBriefId as number),
    enabled: !!slug && playbookId != null && activeBriefId != null,
  });

  const generate = () => {
    if (playbookId == null) return;
    create.mutate(
      { id: playbookId, body: { stress_run_id: stressRunId } },
      { onSuccess: (brief) => setActiveBriefId(brief.id) },
    );
  };

  const brief = create.data && create.data.id === activeBriefId ? create.data : briefQuery.data;

  const exportUrls = useMemo(() => {
    if (!slug || playbookId == null || activeBriefId == null) return null;
    return {
      html: api.briefExportUrl(slug, playbookId, activeBriefId, "html"),
      pdf: api.briefExportUrl(slug, playbookId, activeBriefId, "pdf"),
    };
  }, [slug, playbookId, activeBriefId]);

  if (!slug) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        {t("act.noScenario")}
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 gap-3 p-3">
      {/* Controls rail */}
      <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto rounded-lg border border-border bg-surface p-3">
        <div>
          <h2 className="mb-2 text-sm font-semibold text-foreground">{t("act.pickPlaybook")}</h2>
          {playbooks.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : playbooks.data && playbooks.data.length > 0 ? (
            <ul className="flex flex-col gap-1">
              {playbooks.data.map((pb) => (
                <li key={pb.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setPlaybookId(pb.id);
                      setActiveBriefId(null);
                    }}
                    className={cn(
                      "flex w-full flex-col rounded-md border px-2.5 py-2 text-left transition-colors",
                      pb.id === playbookId
                        ? "border-primary/50 bg-primary/10"
                        : "border-border bg-surface-raised hover:bg-accent",
                    )}
                  >
                    <span className="truncate text-sm font-medium text-foreground">{pb.name}</span>
                    <span className="font-mono text-2xs text-muted-foreground">
                      {t("decide.score")}:{" "}
                      {pb.score_result ? pb.score_result.overall.toFixed(1) : "—"}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-2xs text-muted-foreground">{t("act.noPlaybooks")}</p>
          )}
        </div>

        {playbookId != null && (
          <div>
            <h3 className="mb-1.5 text-2xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t("act.robustnessLabel")}
            </h3>
            {runs.data && runs.data.length > 0 ? (
              <select
                value={stressRunId ?? ""}
                onChange={(e) => setStressRunId(e.target.value ? Number(e.target.value) : null)}
                className="w-full rounded-md border border-input bg-surface-raised px-2 py-1.5 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {runs.data.map((r) => (
                  <option key={r.id} value={r.id}>
                    {t("act.runOption", {
                      seed: r.seed,
                      n: r.n_iterations,
                      date: new Date(r.created_at).toLocaleDateString(),
                    })}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-2xs text-muted-foreground">{t("act.noStress")}</p>
            )}
          </div>
        )}

        <Button onClick={generate} disabled={playbookId == null || create.isPending}>
          {create.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : brief ? (
            <RefreshCw className="h-4 w-4" />
          ) : (
            <Dices className="h-4 w-4" />
          )}
          {brief ? t("act.regenerate") : t("act.generate")}
        </Button>
        {create.isError && <p className="text-2xs text-signal-crit">{t("act.generateError")}</p>}
      </aside>

      {/* Document */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-lg border border-border bg-surface">
        <div className="flex items-center justify-end gap-2 border-b border-border px-3 py-2">
          {exportUrls && brief && (
            <>
              <a
                href={exportUrls.html}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent"
              >
                <FileText className="h-3.5 w-3.5" />
                {t("act.exportHtml")}
              </a>
              <a
                href={exportUrls.pdf}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
              >
                <Download className="h-3.5 w-3.5" />
                {t("act.exportPdf")}
              </a>
            </>
          )}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-5">
          {create.isPending || briefQuery.isLoading ? (
            <div className="mx-auto flex max-w-3xl flex-col gap-3">
              <Skeleton className="h-8 w-2/3" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : brief ? (
            <BriefDocument brief={brief} />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
              <FileText className="h-8 w-8 opacity-40" />
              <p className="text-sm">{t("act.emptyState")}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
