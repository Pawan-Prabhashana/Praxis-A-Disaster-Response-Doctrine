import { cn } from "@/lib/utils";

/**
 * Praxis logo mark — a rounded square enclosing a broken loop with a leading
 * node, evoking the continuous Sense → Decide → Act → Learn cycle. Uses
 * `currentColor` for the loop and the primary token for the leading node so it
 * adapts to theme and context.
 */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("h-7 w-7", className)}
      role="img"
      aria-label="Praxis"
    >
      <rect
        x="1"
        y="1"
        width="30"
        height="30"
        rx="8"
        className="fill-surface-raised stroke-border"
        strokeWidth="1.5"
      />
      <path
        d="M16 8a8 8 0 1 1-7.4 5"
        className="stroke-foreground"
        strokeWidth="2.25"
        strokeLinecap="round"
      />
      <circle cx="16" cy="8" r="2.75" className="fill-primary" />
    </svg>
  );
}

/** Full wordmark: mark + product name, for the top bar. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <LogoMark />
      <div className="flex flex-col leading-none">
        <span className="text-sm font-semibold tracking-tight text-foreground">Praxis</span>
        <span className="text-2xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
          Command
        </span>
      </div>
    </div>
  );
}
