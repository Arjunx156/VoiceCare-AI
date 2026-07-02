import { describe, expect, it } from "vitest";

import {
  PRIORITY_META,
  SENTIMENT_META,
  STATUS_META,
  priorityMeta,
  sentimentMeta,
  statusMeta,
} from "./theme";

describe("theme meta maps", () => {
  it("covers every ticket priority", () => {
    for (const key of ["Critical", "High", "Medium", "Low"]) {
      expect(PRIORITY_META[key]).toBeDefined();
      expect(PRIORITY_META[key].fg).toBeTruthy();
      expect(PRIORITY_META[key].bg).toBeTruthy();
    }
  });

  it("covers every ticket status", () => {
    for (const key of ["Open", "In Progress", "Resolved", "Escalated", "Closed"]) {
      expect(STATUS_META[key]).toBeDefined();
    }
  });

  it("covers every sentiment the pipeline emits", () => {
    for (const key of ["Positive", "Neutral", "Calm", "Confused", "Negative", "Angry", "Very Angry"]) {
      expect(SENTIMENT_META[key]).toBeDefined();
    }
  });

  it("falls back safely for unknown or missing values", () => {
    for (const accessor of [priorityMeta, statusMeta, sentimentMeta]) {
      expect(accessor("Nonsense").fg).toBeTruthy();
      expect(accessor(null).fg).toBeTruthy();
      expect(accessor(undefined).bg).toBeTruthy();
    }
  });
});
