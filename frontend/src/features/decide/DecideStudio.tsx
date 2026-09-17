import { GitCompareArrows, PencilRuler } from "lucide-react";
import { useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";

import { PlaybookList } from "@/features/decide/PlaybookList";
import { PlaybookBuilder } from "@/features/decide/builder/PlaybookBuilder";
import { CompareView } from "@/features/decide/compare/CompareView";
import { usePlaybookDefaults } from "@/features/decide/hooks";
import { useDecideStore } from "@/features/decide/store";
import { useScenarioDetail } from "@/features/sense/hooks";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

export function DecideStudio() {
  const { t } = useTranslation();
  const slug = useUiStore((s) => s.selectedScenarioSlug);

  const detail = useScenarioDetail(slug);
  const defaults = usePlaybookDefaults(slug);
  const mode = useDecideStore((s) => s.mode);
  const setMode = useDecideStore((s) => s.setMode);
  const draft = useDecideStore((s) => s.draft);
  const editingId = useDecideStore((s) => s.editingId);
  const startNew = useDecideStore((s) => s.startNew);

  // Seed the builder with data-driven defaults once, for a smart empty start.
  const seeded = useRef(false);
  useEffect(() => {
    if (
      !seeded.current &&
      defaults.data &&
      editingId === null &&
      draft.levers.priority_region_pcodes.length === 0
    ) {
      seeded.current = true;
      startNew(defaults.data);
    }
  }, [defaults.data, editingId, draft.levers.priority_region_pcodes.length, startNew]);

  const bbox = useMemo<[number, number, number, number] | null>(() => {
    const b = detail.data?.bbox;
    return b ? [b.min_lon, b.min_lat, b.max_lon, b.max_lat] : null;
  }, [detail.data]);

  if (!slug) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-muted-foreground">
        {t("decide.noScenario")}
      </div>
    );
  }

  const tabs = [
    { key: "builder" as const, label: t("decide.builderTab"), icon: PencilRuler },
    { key: "compare" as const, label: t("decide.compareTab"), icon: GitCompareArrows },
  ];

  return (
    <div className="flex h-full flex-col gap-3 p-3">
      <div className="flex items-center gap-1 rounded-lg border border-border bg-surface p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = mode === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setMode(tab.key)}
              className={cn(
                "flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
        <span className="ml-auto pr-2 text-2xs text-muted-foreground">
          {detail.data?.name ?? ""}
        </span>
      </div>

      <div className="flex min-h-0 flex-1 gap-3">
        <aside className="hidden w-64 shrink-0 overflow-hidden rounded-lg border border-border bg-surface md:block">
          <PlaybookList slug={slug} />
        </aside>

        <div className="min-w-0 flex-1">
          {mode === "builder" ? (
            <PlaybookBuilder slug={slug} bbox={bbox} />
          ) : (
            <CompareView slug={slug} />
          )}
        </div>
      </div>
    </div>
  );
}
