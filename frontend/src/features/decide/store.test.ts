import { beforeEach, describe, expect, it } from "vitest";

import { EMPTY_LEVERS, useDecideStore } from "@/features/decide/store";

function reset() {
  useDecideStore.setState({
    mode: "builder",
    editingId: null,
    draft: { name: "", description: "", levers: EMPTY_LEVERS },
    compareIds: [],
  });
}

describe("useDecideStore", () => {
  beforeEach(reset);

  it("patchLevers merges into the draft lever set (shaping the score request)", () => {
    useDecideStore.getState().patchLevers({ priority_region_pcodes: ["LK11", "LK13"] });
    useDecideStore.getState().patchLevers({
      resources: { response_teams: 10, boats: 4, allocation: "even" },
    });
    const levers = useDecideStore.getState().draft.levers;
    expect(levers.priority_region_pcodes).toEqual(["LK11", "LK13"]);
    expect(levers.resources.response_teams).toBe(10);
    // untouched levers are preserved
    expect(levers.access.avoid_closed_roads).toBe(true);
  });

  it("toggleCompare adds/removes and caps the selection at three", () => {
    const { toggleCompare } = useDecideStore.getState();
    toggleCompare(1);
    toggleCompare(2);
    toggleCompare(3);
    toggleCompare(4); // ignored — cap of 3
    expect(useDecideStore.getState().compareIds).toEqual([1, 2, 3]);
    toggleCompare(2); // remove
    expect(useDecideStore.getState().compareIds).toEqual([1, 3]);
  });
});
