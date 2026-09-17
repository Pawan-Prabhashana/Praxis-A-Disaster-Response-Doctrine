interface BandBarProps {
  p05: number;
  median: number;
  p95: number;
  point: number;
  color: string;
  /** 0..100 scale marker for the robustness target. */
  target?: number;
}

const clamp = (v: number) => Math.max(0, Math.min(100, v));

/**
 * A horizontal 0–100 band: the p05–p95 range as a bar, the median as a solid
 * marker, and the deterministic point score as a hollow marker — so overlapping
 * bands across strategies are directly comparable.
 */
export function BandBar({ p05, median, p95, point, color, target }: BandBarProps) {
  return (
    <div className="relative h-6 w-full rounded bg-muted/60">
      {target != null && (
        <div
          className="absolute top-0 h-full w-px bg-primary/70"
          style={{ left: `${clamp(target)}%` }}
          aria-hidden
        />
      )}
      <div
        className="absolute top-1 h-4 rounded"
        style={{
          left: `${clamp(p05)}%`,
          width: `${clamp(p95) - clamp(p05)}%`,
          background: color,
          opacity: 0.35,
        }}
      />
      {/* point score (hollow) */}
      <div
        className="absolute top-0.5 h-5 w-1 rounded-sm border"
        style={{ left: `${clamp(point)}%`, borderColor: color, background: "transparent" }}
        title={`point ${point}`}
      />
      {/* median (solid) */}
      <div
        className="absolute top-0 h-full w-1 rounded-sm"
        style={{ left: `${clamp(median)}%`, background: color }}
        title={`median ${median}`}
      />
    </div>
  );
}
