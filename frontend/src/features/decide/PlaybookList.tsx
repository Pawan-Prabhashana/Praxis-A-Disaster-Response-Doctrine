import { Copy, Plus, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCreatePlaybook,
  useDeletePlaybook,
  usePlaybookDefaults,
  usePlaybooks,
} from "@/features/decide/hooks";
import { EMPTY_LEVERS, useDecideStore } from "@/features/decide/store";
import type { Playbook } from "@/lib/api";
import { cn } from "@/lib/utils";

export function PlaybookList({ slug }: { slug: string }) {
  const { t } = useTranslation();
  const playbooks = usePlaybooks(slug);
  const defaults = usePlaybookDefaults(slug);
  const create = useCreatePlaybook(slug);
  const remove = useDeletePlaybook(slug);

  const mode = useDecideStore((s) => s.mode);
  const editingId = useDecideStore((s) => s.editingId);
  const startNew = useDecideStore((s) => s.startNew);
  const editPlaybook = useDecideStore((s) => s.editPlaybook);
  const compareIds = useDecideStore((s) => s.compareIds);
  const toggleCompare = useDecideStore((s) => s.toggleCompare);

  const onNew = () => startNew(defaults.data ?? EMPTY_LEVERS);

  const onDuplicate = (pb: Playbook) => {
    create.mutate({ name: `${pb.name} ${t("decide.copySuffix")}`, levers: pb.levers });
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-3 py-3">
        <h2 className="text-sm font-semibold text-foreground">{t("decide.playbooks")}</h2>
        <Button size="sm" variant="secondary" onClick={onNew}>
          <Plus className="h-4 w-4" />
          {t("decide.new")}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {playbooks.isLoading ? (
          <div className="flex flex-col gap-2 p-1">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : playbooks.data && playbooks.data.length > 0 ? (
          <ul className="flex flex-col gap-1">
            {playbooks.data.map((pb) => {
              const selectedForCompare = compareIds.includes(pb.id);
              const isEditing = editingId === pb.id && mode === "builder";
              return (
                <li key={pb.id}>
                  <div
                    className={cn(
                      "group flex items-center gap-2 rounded-md border px-2.5 py-2 transition-colors",
                      isEditing
                        ? "border-primary/50 bg-primary/10"
                        : "border-border bg-surface-raised hover:bg-accent",
                    )}
                  >
                    {mode === "compare" && (
                      <input
                        type="checkbox"
                        checked={selectedForCompare}
                        onChange={() => toggleCompare(pb.id)}
                        aria-label={t("decide.selectForCompare")}
                        className="h-4 w-4 shrink-0 accent-[hsl(var(--primary))]"
                      />
                    )}
                    <button
                      type="button"
                      onClick={() => (mode === "compare" ? toggleCompare(pb.id) : editPlaybook(pb))}
                      className="flex min-w-0 flex-1 flex-col text-left focus-visible:outline-none"
                    >
                      <span className="truncate text-sm font-medium text-foreground">
                        {pb.name}
                      </span>
                      <span className="font-mono text-2xs text-muted-foreground">
                        {t("decide.score")}:{" "}
                        {pb.score_result ? pb.score_result.overall.toFixed(1) : "—"}
                      </span>
                    </button>
                    <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                      <button
                        type="button"
                        onClick={() => onDuplicate(pb)}
                        aria-label={t("decide.duplicate")}
                        className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
                      >
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => remove.mutate(pb.id)}
                        aria-label={t("decide.delete")}
                        className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-signal-crit"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="px-2 py-4 text-2xs text-muted-foreground">{t("decide.noPlaybooks")}</p>
        )}
      </div>
    </div>
  );
}
