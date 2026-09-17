import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import type { RegionContext } from "@/lib/api";
import { cn } from "@/lib/utils";

interface RegionPickerProps {
  regions: RegionContext[];
  selected: string[];
  onToggle: (pcode: string) => void;
}

export function RegionPicker({ regions, selected, onToggle }: RegionPickerProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const filtered = regions.filter((r) => r.name.toLowerCase().includes(query.toLowerCase()));
  const selectedSet = new Set(selected);

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={t("decide.regionSearch")}
        className="mb-2 w-full rounded-md border border-input bg-surface-raised px-2.5 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
      <ul className="flex max-h-56 flex-col gap-1 overflow-y-auto pr-1">
        {filtered.map((r) => {
          const on = selectedSet.has(r.pcode);
          return (
            <li key={r.pcode}>
              <button
                type="button"
                role="switch"
                aria-checked={on}
                onClick={() => onToggle(r.pcode)}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md border px-2.5 py-1.5 text-left transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  on
                    ? "border-primary/50 bg-primary/10"
                    : "border-border bg-surface-raised hover:bg-accent",
                )}
              >
                <span
                  className={cn(
                    "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
                    on ? "border-primary bg-primary" : "border-muted-foreground",
                  )}
                  aria-hidden
                >
                  {on && <span className="h-2 w-2 rounded-sm bg-primary-foreground" />}
                </span>
                <span className="flex flex-1 flex-col">
                  <span className="flex items-center gap-1.5">
                    <span className="text-sm text-foreground">{r.name}</span>
                    {r.is_access_impaired && <Badge variant="warn">{t("decide.accessTag")}</Badge>}
                  </span>
                  <span className="font-mono text-2xs text-muted-foreground">
                    {t("decide.atRisk")}: {r.at_risk_population.toLocaleString()} ·{" "}
                    {t("decide.pop")}: {r.population.toLocaleString()}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
        {filtered.length === 0 && (
          <li className="px-1 py-2 text-2xs text-muted-foreground">{t("decide.noRegions")}</li>
        )}
      </ul>
    </div>
  );
}
