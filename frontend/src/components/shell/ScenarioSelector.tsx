import { Check, ChevronsUpDown, Layers } from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useScenarios } from "@/hooks/useScenarios";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

/**
 * Global scenario selector, wired to GET /api/v1/scenarios. Lists the real
 * seeded scenarios and stores the active selection in the UI store. (Map and
 * data layers arrive in Phase 3 — this only selects the scenario.)
 */
export function ScenarioSelector() {
  const { t } = useTranslation();
  const { data: scenarios, isLoading, isError } = useScenarios();
  const selectedSlug = useUiStore((s) => s.selectedScenarioSlug);
  const setSelected = useUiStore((s) => s.setSelectedScenario);

  // Default to the first scenario once loaded and nothing is selected yet.
  useEffect(() => {
    if (!selectedSlug && scenarios && scenarios.length > 0) {
      setSelected(scenarios[0]?.slug ?? null);
    }
  }, [scenarios, selectedSlug, setSelected]);

  const selected = scenarios?.find((s) => s.slug === selectedSlug) ?? null;
  const label = isLoading
    ? t("scenario.loading")
    : isError
      ? t("scenario.error")
      : (selected?.name ?? t("scenario.placeholder"));

  const hasScenarios = !!scenarios && scenarios.length > 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="group flex min-w-[13rem] max-w-[22rem] items-center gap-2.5 rounded-md border border-border bg-surface-raised px-3 py-1.5 text-left transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <Layers className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="flex flex-1 flex-col overflow-hidden leading-tight">
            <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
              {t("scenario.label")}
            </span>
            <span className="truncate text-sm font-medium text-foreground">{label}</span>
          </span>
          <ChevronsUpDown className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[22rem]">
        <DropdownMenuLabel>{t("scenario.label")}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {!hasScenarios && (
          <DropdownMenuItem disabled className="text-muted-foreground">
            {isLoading ? t("scenario.loading") : t("scenario.empty")}
          </DropdownMenuItem>
        )}
        {scenarios?.map((scenario) => (
          <DropdownMenuItem
            key={scenario.slug}
            onSelect={() => setSelected(scenario.slug)}
            className="flex items-start gap-2"
          >
            <Check
              className={cn(
                "mt-0.5 h-4 w-4 shrink-0 text-primary",
                scenario.slug === selectedSlug ? "opacity-100" : "opacity-0",
              )}
            />
            <span className="flex flex-col">
              <span className="text-sm text-foreground">{scenario.name}</span>
              <span className="text-2xs uppercase tracking-wider text-muted-foreground">
                {scenario.hazard_type} · {scenario.status}
                {scenario.event_date ? ` · ${scenario.event_date}` : ""}
              </span>
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
