import { describe, expect, it } from "vitest";

import { bestInRow } from "@/features/decide/compare/logic";

describe("bestInRow", () => {
  it("flags the single highest value", () => {
    expect(bestInRow([0.2, 0.8, 0.5])).toEqual([false, true, false]);
  });

  it("flags ties", () => {
    expect(bestInRow([0.6, 0.6, 0.3])).toEqual([true, true, false]);
  });

  it("highlights nothing when all values are zero", () => {
    expect(bestInRow([0, 0, 0])).toEqual([false, false, false]);
  });
});
