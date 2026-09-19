import { useEffect } from "react";
import { Outlet } from "react-router-dom";

import { OfflineBanner } from "@/components/shell/OfflineBanner";
import { Sidebar } from "@/components/shell/Sidebar";
import { Topbar } from "@/components/shell/Topbar";
import { applyTheme, useUiStore } from "@/store/ui";

/**
 * The application frame: top bar, left navigation, and the routed workspace.
 * Owns the theme side-effect so the document root always matches the store.
 */
export function AppShell() {
  const theme = useUiStore((s) => s.theme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Topbar />
      <OfflineBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
