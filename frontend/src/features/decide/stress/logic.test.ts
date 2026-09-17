import { describe, expect, it } from "vitest";

import { type StressEntry, analyseWinners } from "@/features/decide/stress/logic";

describe("analyseWinners", () => {
  it("flags a reversal when the robust winner is not the point winner", () => {
    const entries: StressEntry[] = [
      { id: 1, name: "Aggressive", point: 70, median: 55, p05: 40, p95: 78 },
      { id: 2, name: "Robust", point: 66, median: 63, p05: 58, p95: 70 },
    ];
    const r = analyseWinners(entries);
    expect(r.pointWinnerId).toBe(1); // highest point score
    expect(r.robustWinnerId).toBe(2); // highest worst-plausible (p05)
    expect(r.reversal).toBe(true);
  });

  it("no reversal when the same strategy wins on both", () => {
    const entries: StressEntry[] = [
      { id: 1, name: "A", point: 80, median: 75, p05: 70, p95: 85 },
      { id: 2, name: "B", point: 60, median: 55, p05: 50, p95: 65 },
    ];
    const r = analyseWinners(entries);
    expect(r.pointWinnerId).toBe(1);
    expect(r.robustWinnerId).toBe(1);
    expect(r.reversal).toBe(false);
  });

  it("returns no winners for fewer than two entries", () => {
    const r = analyseWinners([{ id: 1, name: "A", point: 50, median: 50, p05: 40, p95: 60 }]);
    expect(r.reversal).toBe(false);
    expect(r.robustWinnerId).toBeNull();
  });
});
