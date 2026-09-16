import { Wordmark } from "@/components/shell/Logo";
import { ScenarioSelector } from "@/components/shell/ScenarioSelector";
import { SystemStatus } from "@/components/shell/SystemStatus";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { Separator } from "@/components/ui/separator";

/**
 * Global top bar: product identity, the active-scenario selector, and the live
 * system-status indicator. Fixed height, sits above the sidebar + workspace.
 */
export function Topbar() {
  return (
    <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-surface px-4">
      <div className="flex w-56 items-center">
        <Wordmark />
      </div>

      <Separator orientation="vertical" className="h-8" />

      <ScenarioSelector />

      <div className="ml-auto flex items-center gap-2">
        <SystemStatus />
        <Separator orientation="vertical" className="h-6" />
        <ThemeToggle />
      </div>
    </header>
  );
}
