import { useTranslation } from "react-i18next";

import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

type Tone = "ok" | "crit" | "pending";

const TONE_DOT: Record<Tone, string> = {
  ok: "bg-signal-ok",
  crit: "bg-signal-crit",
  pending: "bg-muted-foreground",
};

/**
 * Live API + database status pill. Polls `/health` and reflects the real
 * backend state: online (API + DB healthy), degraded (API up, DB error), or
 * offline (unreachable). A tooltip exposes the detailed readout.
 */
export function SystemStatus() {
  const { t } = useTranslation();
  const { data, isLoading, isError, dataUpdatedAt } = useHealth();

  const apiOnline = !isError && !!data;
  const dbOk = data?.db === "ok";

  let tone: Tone = "pending";
  let label = t("status.checking");
  if (!isLoading) {
    if (apiOnline) {
      tone = dbOk ? "ok" : "crit";
      label = t("status.online");
    } else {
      tone = "crit";
      label = t("status.offline");
    }
  }

  const lastChecked =
    dataUpdatedAt > 0 ? new Date(dataUpdatedAt).toLocaleTimeString([], { hour12: false }) : "—";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-md border border-border bg-surface-raised px-2.5 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-accent"
          aria-label={label}
        >
          <span className="relative flex h-2 w-2">
            {tone === "ok" && (
              <span className="absolute inline-flex h-full w-full animate-pulse-signal rounded-full bg-signal-ok/70" />
            )}
            <span className={cn("relative inline-flex h-2 w-2 rounded-full", TONE_DOT[tone])} />
          </span>
          <span className="hidden sm:inline">{label}</span>
        </button>
      </TooltipTrigger>
      <TooltipContent align="end" className="w-56 p-0">
        <div className="px-3 py-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">{t("app.name")} API</span>
            <span
              className={cn(
                "font-mono text-2xs uppercase",
                apiOnline ? "text-signal-ok" : "text-signal-crit",
              )}
            >
              {apiOnline ? "200 OK" : "unreachable"}
            </span>
          </div>
        </div>
        <Separator />
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 px-3 py-2 font-mono text-2xs">
          <dt className="text-muted-foreground">{t("status.db")}</dt>
          <dd className={cn("text-right", dbOk ? "text-signal-ok" : "text-signal-crit")}>
            {data?.db ?? "—"}
          </dd>
          <dt className="text-muted-foreground">{t("status.version")}</dt>
          <dd className="text-right text-foreground">{data?.version ?? "—"}</dd>
          <dt className="text-muted-foreground">{t("status.lastChecked")}</dt>
          <dd className="text-right text-foreground">{lastChecked}</dd>
        </dl>
      </TooltipContent>
    </Tooltip>
  );
}
