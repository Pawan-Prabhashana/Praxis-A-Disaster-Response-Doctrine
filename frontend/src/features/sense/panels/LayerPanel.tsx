import { Database, Info } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { LAYER_DEFS, type LayerKey } from "@/features/sense/layers";
import type { AdminLevel } from "@/features/sense/store";
import type { SourceInfo } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Per-layer legend swatch: color + shape, dashed border when synthetic. */
function Swatch({ layer }: { layer: LayerKey }) {
  const base = "inline-block h-3 w-3 shrink-0";
  switch (layer) {
    case "admin":
      return (
        <span
          className={cn(base, "rounded-sm")}
          style={{ background: "hsl(var(--primary) / 0.45)" }}
        />
      );
    case "flood":
      return (
        <span
          className={cn(base, "rounded-sm")}
          style={{ background: "hsl(var(--signal-info) / 0.5)" }}
        />
      );
    case "landslide":
      return (
        <span
          className={cn(base, "rounded-sm border border-dashed")}
          style={{
            background: "hsl(var(--signal-warn) / 0.25)",
            borderColor: "hsl(var(--signal-warn))",
          }}
        />
      );
    case "roads":
      return (
        <span className="inline-flex h-3 w-3 items-center">
          <span className="h-0.5 w-3" style={{ background: "hsl(var(--muted-foreground))" }} />
        </span>
      );
    case "shelters":
      return (
        <span
          className={cn(base, "rounded-full")}
          style={{ background: "hsl(var(--signal-ok))" }}
        />
      );
    case "incidents":
      return (
        <span
          className={cn(base, "rounded-full")}
          style={{ background: "hsl(var(--signal-warn))" }}
        />
      );
    case "rivers":
      return (
        <span
          className={cn(base, "rounded-full border-2")}
          style={{ borderColor: "hsl(var(--signal-info))", background: "transparent" }}
        />
      );
  }
}

interface LayerPanelProps {
  visibility: Record<LayerKey, boolean>;
  counts: Partial<Record<LayerKey, number | undefined>>;
  onToggle: (key: LayerKey) => void;
  adminLevel: AdminLevel;
  onAdminLevel: (level: AdminLevel) => void;
  sources: SourceInfo[];
}

export function LayerPanel({
  visibility,
  counts,
  onToggle,
  adminLevel,
  onAdminLevel,
  sources,
}: LayerPanelProps) {
  const { t } = useTranslation();

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">{t("sense.layers.title")}</h2>
        <Info className="h-4 w-4 text-muted-foreground" aria-hidden />
      </div>
      <Separator />

      <div className="flex-1 overflow-y-auto p-2">
        <ul className="flex flex-col gap-0.5">
          {LAYER_DEFS.map((def) => {
            const on = visibility[def.key];
            const count = counts[def.key];
            return (
              <li key={def.key}>
                <button
                  type="button"
                  role="switch"
                  aria-checked={on}
                  onClick={() => onToggle(def.key)}
                  className={cn(
                    "flex w-full items-start gap-2.5 rounded-md px-2 py-2 text-left transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    on ? "bg-accent/50" : "opacity-55 hover:opacity-90 hover:bg-accent/30",
                  )}
                >
                  <span className="mt-0.5">
                    <Swatch layer={def.key} />
                  </span>
                  <span className="flex flex-1 flex-col">
                    <span className="flex items-center gap-1.5">
                      <span className="text-sm font-medium text-foreground">{t(def.labelKey)}</span>
                      {def.synthetic && <Badge variant="warn">sample</Badge>}
                      {def.partialSynthetic && <Badge variant="outline">partial sample</Badge>}
                    </span>
                    <span className="text-2xs text-muted-foreground">{t(def.noteKey)}</span>
                  </span>
                  <span className="ml-1 font-mono text-2xs tabular-nums text-muted-foreground">
                    {count != null ? count.toLocaleString() : "—"}
                  </span>
                </button>

                {def.key === "admin" && on && (
                  <div className="ml-8 mb-1 flex items-center gap-1">
                    {([2, 3] as const).map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => onAdminLevel(lvl)}
                        className={cn(
                          "rounded px-2 py-0.5 text-2xs font-medium transition-colors",
                          adminLevel === lvl
                            ? "bg-primary/20 text-primary"
                            : "text-muted-foreground hover:bg-accent",
                        )}
                      >
                        {t(lvl === 2 ? "sense.layers.adminDistrict" : "sense.layers.adminDivision")}
                      </button>
                    ))}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>

      <Separator />
      <div className="p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex w-full items-center gap-2 rounded-md border border-border bg-surface-raised px-3 py-2 text-xs font-medium text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <Database className="h-4 w-4 text-muted-foreground" />
              {t("sense.provenance.button")}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="max-h-80 w-80 overflow-y-auto">
            <DropdownMenuLabel>{t("sense.provenance.title")}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {sources.length === 0 && (
              <div className="px-2 py-1.5 text-2xs text-muted-foreground">
                {t("sense.provenance.empty")}
              </div>
            )}
            {sources.map((s) => (
              <div key={s.key} className="flex items-start gap-2 px-2 py-1.5">
                <span
                  className={cn(
                    "mt-1 h-2 w-2 shrink-0 rounded-full",
                    s.is_synthetic ? "bg-signal-warn" : "bg-signal-ok",
                  )}
                />
                <div className="flex flex-col">
                  <span className="text-2xs font-medium text-foreground">{s.name}</span>
                  <span className="text-2xs text-muted-foreground">
                    {s.is_synthetic ? t("sense.provenance.sample") : t("sense.provenance.real")}
                    {s.license ? ` · ${s.license}` : ""}
                  </span>
                </div>
              </div>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
