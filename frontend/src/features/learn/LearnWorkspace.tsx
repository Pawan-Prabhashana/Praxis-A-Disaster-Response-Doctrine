import { useQuery } from "@tanstack/react-query";
import { GraduationCap, Loader2, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { usePlaybooks } from "@/features/decide/hooks";
import { AfterActionView } from "@/features/learn/AfterActionView";
import { useAfterActions, useCreateAfterAction } from "@/features/learn/hooks";
import { useScenarioDetail } from "@/features/sense/hooks";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

export function LearnWorkspace() {
  const { t } = useTranslation();
  const slug = useUiStore((s) => s.selectedScenarioSlug);

  const playbooks = usePlaybooks(slug);
  const detail = useScenarioDetail(slug);
  const [playbookId, setPlaybookId] = useState<number | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);

  useEffect(() => {
    if (playbookId == null && playbooks.data && playbooks.data.length > 0) {
      setPlaybookId(playbooks.data[0]?.id ?? null);
    }
  }, [playbooks.data, playbookId]);

  const reviews = useAfterActions(slug, playbookId);
  const create = useCreateAfterAction(slug ?? "");

  useEffect(() => {
    setActiveId(reviews.data && reviews.data.length > 0 ? (reviews.data[0]?.id ?? null) : null);
  }, [reviews.data]);

  const aaQuery = useQuery({
    queryKey: ["after-action", slug, playbookId, activeId],
    queryFn: () => api.getAfterAction(slug as string, playbookId as number, activeId as number),
    enabled: !!slug && playbookId != null && activeId != null,
  });

  const aa = create.data && create.data.id === activeId ? create.data : aaQuery.data;

  const bbox = useMemo<[number, number, number, number] | null>(() => {
    const b = detail.data?.bbox;
    return b ? [b.min_lon, b.min_lat, b.max_lon, b.max_lat] : null;
  }, [detail.data]);

  const generate = () => {
    if (playbookId == null) return;
    create.mutate({ id: playbookId, body: {} }, { onSuccess: (r) => setActiveId(r.id) });
  };

  if (!slug) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        {t("learn.noScenario")}
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 gap-3 p-3">
      <aside className="flex w-72 shrink-0 flex-col gap-4 overflow-y-auto rounded-lg border border-border bg-surface p-3">
        <div>
          <h2 className="mb-2 text-sm font-semibold text-foreground">{t("learn.pickPlaybook")}</h2>
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
                      setActiveId(null);
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
            <p className="text-2xs text-muted-foreground">{t("learn.noPlaybooks")}</p>
          )}
        </div>

        <Button onClick={generate} disabled={playbookId == null || create.isPending}>
          {create.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {aa ? t("learn.regenerate") : t("learn.generate")}
        </Button>
        {create.isError && <p className="text-2xs text-signal-crit">{t("learn.generateError")}</p>}
      </aside>

      <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-border bg-surface p-5">
        {create.isPending || aaQuery.isLoading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-10 w-2/3" />
            <Skeleton className="h-56 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : aa ? (
          <AfterActionView aa={aa} bbox={bbox} />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <GraduationCap className="h-8 w-8 opacity-40" />
            <p className="text-sm">{t("learn.emptyState")}</p>
          </div>
        )}
      </div>
    </div>
  );
}
