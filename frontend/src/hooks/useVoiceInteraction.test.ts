import { describe, expect, it } from "vitest";

import { pairHistoryTurns } from "./useVoiceInteraction";

describe("pairHistoryTurns", () => {
  it("pairs alternating customer/ai turns into exchanges", () => {
    const paired = pairHistoryTurns([
      { role: "customer", content: "Where is my order?" },
      { role: "ai", content: "It ships tomorrow." },
      { role: "customer", content: "Thanks!" },
      { role: "ai", content: "Happy to help." },
    ]);
    expect(paired).toEqual([
      { customer: "Where is my order?", aiText: "It ships tomorrow." },
      { customer: "Thanks!", aiText: "Happy to help." },
    ]);
  });

  it("keeps an ai reply without a preceding customer message", () => {
    const paired = pairHistoryTurns([{ role: "ai", content: "Hello!" }]);
    expect(paired).toEqual([{ customer: "", aiText: "Hello!" }]);
  });

  it("keeps consecutive customer messages as separate turns", () => {
    const paired = pairHistoryTurns([
      { role: "customer", content: "First message" },
      { role: "customer", content: "Second message" },
      { role: "ai", content: "Reply to second" },
    ]);
    expect(paired).toEqual([
      { customer: "First message", aiText: "" },
      { customer: "Second message", aiText: "Reply to second" },
    ]);
  });

  it("keeps a trailing unanswered customer message", () => {
    const paired = pairHistoryTurns([
      { role: "customer", content: "Anyone there?" },
    ]);
    expect(paired).toEqual([{ customer: "Anyone there?", aiText: "" }]);
  });

  it("returns empty for empty history", () => {
    expect(pairHistoryTurns([])).toEqual([]);
  });
});
