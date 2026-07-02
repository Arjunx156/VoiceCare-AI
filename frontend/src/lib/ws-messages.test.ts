import { describe, expect, it } from "vitest";

import { parseWsMessage } from "./ws-messages";

describe("parseWsMessage", () => {
  it("parses pings", () => {
    expect(parseWsMessage(JSON.stringify({ type: "ping" }))).toEqual({ kind: "ping" });
  });

  it("parses stage updates", () => {
    const msg = parseWsMessage(
      JSON.stringify({ stage_number: 3, total_stages: 9, message: "Checking your order..." })
    );
    expect(msg).toEqual({
      kind: "stage",
      stageNumber: 3,
      totalStages: 9,
      message: "Checking your order...",
    });
  });

  it("parses the final response frame", () => {
    const msg = parseWsMessage(
      JSON.stringify({ type: "response", response_text: "Done", is_complete: true })
    );
    expect(msg.kind).toBe("response");
    if (msg.kind === "response") {
      expect(msg.response.response_text).toBe("Done");
    }
  });

  it("parses error frames including retry_after", () => {
    const msg = parseWsMessage(
      JSON.stringify({ error: "RATE_LIMITED", detail: "slow down", retry_after: 60 })
    );
    expect(msg).toEqual({
      kind: "error",
      code: "RATE_LIMITED",
      detail: "slow down",
      retryAfter: 60,
    });
  });

  it("never throws on malformed input", () => {
    expect(parseWsMessage("not json")).toEqual({ kind: "unknown" });
    expect(parseWsMessage("42")).toEqual({ kind: "unknown" });
    expect(parseWsMessage("null")).toEqual({ kind: "unknown" });
    expect(parseWsMessage(JSON.stringify({ something: "else" }))).toEqual({ kind: "unknown" });
  });
});
