import { ChevronsUpDown, Layers } from "lucide-react";
import { useTranslation } from "react-i18next";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/**
 * Global scenario selector. The scenario catalogue is seeded in Phase 2, so
 * this renders a deliberate, designed empty state rather than a dead control —
 * it establishes the placement and interaction the loaded version will inherit.
 */
export function ScenarioSelector() {
  const { t } = useTranslation();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="group flex min-w-[13rem] items-center gap-2.5 rounded-md border border-border bg-surface-raised px-3 py-1.5 text-left transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <Layers className="h-4 w-4 text-muted-foreground" />
          <span className="flex flex-1 flex-col leading-tight">
            <span className="text-2xs font-medium uppercase tracking-wider text-muted-foreground">
              {t("scenario.label")}
            </span>
            <span className="text-sm font-medium text-foreground">{t("scenario.placeholder")}</span>
          </span>
          <ChevronsUpDown className="h-4 w-4 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[13rem]">
        <DropdownMenuLabel>{t("scenario.label")}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled className="text-muted-foreground">
          {t("scenario.empty")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
