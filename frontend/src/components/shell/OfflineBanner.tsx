import { WifiOff } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useOnlineStatus } from "@/hooks/useOnlineStatus";

/**
 * A thin, honest banner shown only while the browser is offline. It makes clear
 * that any data on screen is cached and may not be live — the app never presents
 * stale data as current.
 */
export function OfflineBanner() {
  const { t } = useTranslation();
  const online = useOnlineStatus();
  if (online) return null;
  return (
    <div className="flex items-center justify-center gap-2 bg-signal-warn/15 px-4 py-1.5 text-2xs font-medium text-signal-warn">
      <WifiOff className="h-3.5 w-3.5 shrink-0" />
      <span>
        {t("offline.banner")} {t("offline.tilesNote")}
      </span>
    </div>
  );
}
