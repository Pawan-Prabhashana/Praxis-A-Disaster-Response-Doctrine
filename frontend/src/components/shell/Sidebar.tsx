import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { LOOP_ITEMS, type NavItem, OVERVIEW_ITEM } from "@/config/nav";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/store/ui";

function NavRow({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const { t } = useTranslation();
  const Icon = item.icon;

  const row = (
    <NavLink
      to={item.path}
      end={item.path === "/"}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          isActive
            ? "bg-accent text-foreground"
            : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
          collapsed && "justify-center px-0",
        )
      }
    >
      {({ isActive }) => (
        <>
          <span
            className={cn(
              "absolute left-0 h-5 w-0.5 rounded-full bg-primary transition-opacity",
              isActive ? "opacity-100" : "opacity-0",
            )}
            aria-hidden
          />
          <Icon className="h-4 w-4 shrink-0" />
          {!collapsed && <span className="flex-1">{t(item.labelKey)}</span>}
          {!collapsed && item.ordinal && (
            <span className="font-mono text-2xs text-muted-foreground/70">{item.ordinal}</span>
          )}
        </>
      )}
    </NavLink>
  );

  if (!collapsed) return row;
  return (
    <Tooltip>
      <TooltipTrigger asChild>{row}</TooltipTrigger>
      <TooltipContent side="right">{t(item.labelKey)}</TooltipContent>
    </Tooltip>
  );
}

export function Sidebar() {
  const { t } = useTranslation();
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    <aside
      className={cn(
        "flex shrink-0 flex-col border-r border-border bg-surface transition-[width] duration-200",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="Primary">
        <NavRow item={OVERVIEW_ITEM} collapsed={collapsed} />

        <div className="mt-4 mb-1 px-3">
          {!collapsed && (
            <span className="text-2xs font-semibold uppercase tracking-wider text-muted-foreground/70">
              {t("nav.loopSection")}
            </span>
          )}
        </div>

        <div className="relative flex flex-col gap-1">
          {/* Connective spine implying the continuous loop. */}
          {!collapsed && (
            <span className="absolute left-[1.35rem] top-2 bottom-2 w-px bg-border" aria-hidden />
          )}
          {LOOP_ITEMS.map((item) => (
            <NavRow key={item.path} item={item} collapsed={collapsed} />
          ))}
        </div>
      </nav>

      <div className="border-t border-border p-3">
        <button
          type="button"
          onClick={toggleSidebar}
          className={cn(
            "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
            collapsed && "justify-center px-0",
          )}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
