/** Pure helpers for comparing strategies under uncertainty (unit-tested). */

export interface StressEntry {
  id: number;
  name: string;
  /** Deterministic point score (all params at point values). */
  point: number;
  median: number;
  /** Worst-plausible (p05) — the robustness measure. */
  p05: number;
  p95: number;
}

export interface WinnerAnalysis {
  pointWinnerId: number | null;
  robustWinnerId: number | null;
  /** True when the most-robust strategy is NOT the deterministic top scorer. */
  reversal: boolean;
}

function argmax(entries: StressEntry[], key: (e: StressEntry) => number): number | null {
  let best: StressEntry | null = null;
  for (const e of entries) {
    if (best === null || key(e) > key(best)) best = e;
  }
  return best ? best.id : null;
}

/**
 * The deterministic winner is the highest point score; the robust winner is the
 * highest worst-plausible (p05). A `reversal` — robust winner ≠ point winner — is
 * the most decision-relevant signal the stress test can surface.
 */
export function analyseWinners(entries: StressEntry[]): WinnerAnalysis {
  if (entries.length < 2) {
    return { pointWinnerId: null, robustWinnerId: null, reversal: false };
  }
  const pointWinnerId = argmax(entries, (e) => e.point);
  const robustWinnerId = argmax(entries, (e) => e.p05);
  return { pointWinnerId, robustWinnerId, reversal: pointWinnerId !== robustWinnerId };
}
