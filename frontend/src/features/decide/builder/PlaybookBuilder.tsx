import { Loader2, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { BuilderMap } from "@/features/decide/builder/BuilderMap";
import { RegionPicker } from "@/features/decide/builder/RegionPicker";
import {
  useCreatePlaybook,
  usePlaybookContext,
  usePreviewScore,
  useSheltersInRegions,
  useUpdatePlaybook,
} from "@/features/decide/hooks";
import { Scorecard } from "@/features/decide/scorecard/Scorecard";
import { useDecideStore } from "@/features/decide/store";
import { StressPanel } from "@/features/decide/stress/StressPanel";
import type { AllocationStrategy } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

function NumberField({
  label,
  value,
  onChange,
  min = 0,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="number"
        min={min}
        value={value}
        onChange={(e) => onChange(Math.max(min, Number(e.target.value) || 0))}
        className="w-full rounded-md border border-input bg-surface-raised px-2.5 py-1.5 font-mono text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
    </label>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-4">
      <h3 className="mb-2 text-sm font-semibold text-foreground">{title}</h3>
      {children}
    </section>
  );
}

interface PlaybookBuilderProps {
  slug: string;
  bbox: [number, number, number, number] | null;
}

export function PlaybookBuilder({ slug, bbox }: PlaybookBuilderProps) {
  const { t } = useTranslation();
  const theme = useUiStore((s) => s.theme);
  const draft = useDecideStore((s) => s.draft);
  const editingId = useDecideStore((s) => s.editingId);
  const setDraftName = useDecideStore((s) => s.setDraftName);
  const patchLevers = useDecideStore((s) => s.patchLevers);
  const editPlaybook = useDecideStore((s) => s.editPlaybook);

  const context = usePlaybookContext(slug);
  const preview = usePreviewScore(slug, draft.levers);
  const create = useCreatePlaybook(slug);
  const update = useUpdatePlaybook(slug);

  const levers = draft.levers;
  const [autoShelters, setAutoShelters] = useState(true);
  const [shelterCap, setShelterCap] = useState(200);
  const [bottomTab, setBottomTab] = useState<"live" | "stress">("live");

  const sheltersInRegions = useSheltersInRegions(slug, levers.priority_region_pcodes);

  // Auto-activate shelters within priority regions (capped) when enabled.
  useEffect(() => {
    if (!autoShelters || !sheltersInRegions.data) return;
    const ids = sheltersInRegions.data.ids.slice(0, shelterCap);
    patchLevers({ activated_shelter_ids: ids });
  }, [autoShelters, sheltersInRegions.data, shelterCap, patchLevers]);

  const toggleRegion = (pcode: string) => {
    const set = new Set(levers.priority_region_pcodes);
    if (set.has(pcode)) set.delete(pcode);
    else set.add(pcode);
    patchLevers({ priority_region_pcodes: [...set] });
  };

  const save = () => {
    const body = {
      name: draft.name.trim() || t("decide.untitled"),
      description: draft.description || null,
      levers,
    };
    if (editingId) {
      update.mutate({ id: editingId, body });
    } else {
      create.mutate(body, { onSuccess: (pb) => editPlaybook(pb) });
    }
  };

  const saving = create.isPending || update.isPending;
  const sheltersTotal = sheltersInRegions.data?.total ?? 0;

  return (
    <div className="flex h-full min-h-0 gap-3">
      {/* Lever editor */}
      <div className="w-[22rem] shrink-0 overflow-y-auto rounded-lg border border-border bg-surface p-4">
        <input
          type="text"
          value={draft.name}
          onChange={(e) => setDraftName(e.target.value)}
          placeholder={t("decide.namePlaceholder")}
          className="mb-4 w-full rounded-md border border-input bg-surface-raised px-3 py-2 text-base font-medium text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />

        <Section title={t("decide.priorityRegions")}>
          {context.isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <RegionPicker
              regions={context.data ?? []}
              selected={levers.priority_region_pcodes}
              onToggle={toggleRegion}
            />
          )}
        </Section>

        <Separator className="my-3" />
        <Section title={t("decide.shelterActivation")}>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={autoShelters}
              onChange={(e) => setAutoShelters(e.target.checked)}
              className="h-4 w-4 accent-[hsl(var(--primary))]"
            />
            {t("decide.autoShelters")}
          </label>
          <div className="mt-2">
            <NumberField
              label={t("decide.maxShelters")}
              value={shelterCap}
              onChange={setShelterCap}
              min={0}
            />
          </div>
          <p className="mt-2 text-2xs text-muted-foreground">
            {t("decide.sheltersActivated", {
              active: levers.activated_shelter_ids.length,
              total: sheltersTotal,
            })}
          </p>
          <p className="text-2xs italic text-muted-foreground">{t("decide.capacityNote")}</p>
        </Section>

        <Separator className="my-3" />
        <Section title={t("decide.resources")}>
          <div className="grid grid-cols-2 gap-2">
            <NumberField
              label={t("decide.teams")}
              value={levers.resources.response_teams}
              onChange={(v) =>
                patchLevers({ resources: { ...levers.resources, response_teams: v } })
              }
            />
            <NumberField
              label={t("decide.boats")}
              value={levers.resources.boats}
              onChange={(v) => patchLevers({ resources: { ...levers.resources, boats: v } })}
            />
          </div>
          <label className="mt-2 flex flex-col gap-1">
            <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
              {t("decide.allocation")}
            </span>
            <select
              value={levers.resources.allocation}
              onChange={(e) =>
                patchLevers({
                  resources: {
                    ...levers.resources,
                    allocation: e.target.value as AllocationStrategy,
                  },
                })
              }
              className="w-full rounded-md border border-input bg-surface-raised px-2.5 py-1.5 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="proportional_to_need">{t("decide.allocProportional")}</option>
              <option value="even">{t("decide.allocEven")}</option>
            </select>
          </label>
          <p className="mt-1 text-2xs italic text-muted-foreground">{t("decide.planningNote")}</p>
        </Section>

        <Separator className="my-3" />
        <Section title={t("decide.evacuation")}>
          <NumberField
            label={t("decide.evacThreshold")}
            value={levers.evacuation.at_risk_threshold}
            onChange={(v) => patchLevers({ evacuation: { at_risk_threshold: v } })}
          />
        </Section>

        <Section title={t("decide.access")}>
          <label className="flex items-center gap-2 text-sm text-foreground">
            <input
              type="checkbox"
              checked={levers.access.avoid_closed_roads}
              onChange={(e) => patchLevers({ access: { avoid_closed_roads: e.target.checked } })}
              className="h-4 w-4 accent-[hsl(var(--primary))]"
            />
            {t("decide.avoidClosed")}
          </label>
          <p className="mt-1 text-2xs italic text-muted-foreground">{t("decide.closuresNote")}</p>
        </Section>

        <Button className="mt-2 w-full" onClick={save} disabled={saving}>
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {editingId ? t("decide.saveChanges") : t("decide.savePlaybook")}
        </Button>
      </div>

      {/* Right column: context map on top, live scorecard below (robust at any width) */}
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="min-h-[15rem] flex-1 overflow-hidden rounded-lg border border-border">
          <BuilderMap
            key={theme}
            slug={slug}
            theme={theme}
            bbox={bbox}
            priorityPcodes={levers.priority_region_pcodes}
            activatedShelterIds={levers.activated_shelter_ids}
          />
        </div>

        <div className="max-h-[24rem] shrink-0 overflow-y-auto rounded-lg border border-border bg-surface p-4 lg:max-h-[26rem]">
          <div className="mb-3 flex items-center gap-1 rounded-md border border-border bg-surface-raised p-0.5">
            {(["live", "stress"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setBottomTab(tab)}
                className={cn(
                  "flex flex-1 items-center justify-center gap-1.5 rounded px-2 py-1 text-xs font-medium transition-colors",
                  bottomTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                {tab === "live" ? t("decide.livePreview") : t("decide.stress.tab")}
              </button>
            ))}
          </div>

          {bottomTab === "live" ? (
            <div>
              <div className="mb-2 flex items-center gap-2">
                {preview.isFetching && (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                )}
              </div>
              {preview.data ? (
                <Scorecard result={preview.data} />
              ) : preview.isError ? (
                <p className="text-sm text-signal-crit">{t("decide.scoreError")}</p>
              ) : (
                <Skeleton className="h-64 w-full" />
              )}
            </div>
          ) : (
            <StressPanel slug={slug} playbookId={editingId} />
          )}
        </div>
      </div>
    </div>
  );
}
