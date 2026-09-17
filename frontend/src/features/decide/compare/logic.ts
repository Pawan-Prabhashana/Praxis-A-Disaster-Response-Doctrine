/** Pure comparison helpers (unit-tested). */

/**
 * Flag the best (highest) value(s) in a row across playbooks. Ties all win.
 * A row of all-zero has no winner (nothing to highlight).
 */
export function bestInRow(values: number[]): boolean[] {
  const max = values.reduce((m, v) => Math.max(m, v), 0);
  return values.map((v) => v === max && max > 0);
}
