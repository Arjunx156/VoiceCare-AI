import { describe, expect, it } from "vitest";

import { countAt, easeOutCubic } from "./CountUp";

describe("easeOutCubic", () => {
  it("anchors at 0 and 1", () => {
    expect(easeOutCubic(0)).toBe(0);
    expect(easeOutCubic(1)).toBe(1);
  });

  it("clamps out-of-range progress", () => {
    expect(easeOutCubic(-0.5)).toBe(0);
    expect(easeOutCubic(2)).toBe(1);
  });

  it("eases out (past the midpoint by t=0.5)", () => {
    expect(easeOutCubic(0.5)).toBeGreaterThan(0.5);
  });
});

describe("countAt", () => {
  it("starts at 0 and ends at the target", () => {
    expect(countAt(200, 0, 0)).toBe(0);
    expect(countAt(200, 1, 0)).toBe(200);
  });

  it("rounds to the requested decimals", () => {
    // Non-terminating eased value must round cleanly to 1 dp.
    const v = countAt(37, 0.5, 1);
    expect(Number.isFinite(v)).toBe(true);
    expect(v).toBe(Math.round(v * 10) / 10);
  });

  it("never exceeds the target for in-range progress", () => {
    for (const p of [0, 0.25, 0.5, 0.75, 1]) {
      expect(countAt(100, p, 0)).toBeLessThanOrEqual(100);
    }
  });
});
