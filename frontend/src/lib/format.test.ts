import { describe, expect, it } from "vitest";

import { formatDate, formatDateTime, formatINR, formatRelative } from "./format";

describe("format helpers", () => {
  it("formats dates as short en-IN day + month", () => {
    expect(formatDate("2026-07-02T10:00:00Z")).toMatch(/2 Jul/);
  });

  it("formats date-times with hour and minute", () => {
    const result = formatDateTime("2026-07-02T10:30:00");
    expect(result).toMatch(/2 Jul/);
    expect(result).toMatch(/10:30/);
  });

  it("formats INR without decimals", () => {
    const result = formatINR(2500);
    expect(result).toContain("2,500");
    expect(result).not.toContain(".");
  });

  it("formats relative time for past values", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
    expect(formatRelative(twoHoursAgo)).toMatch(/2 hours ago/);
  });

  it("says 'just now' for sub-minute deltas", () => {
    expect(formatRelative(new Date())).toBe("just now");
  });
});
