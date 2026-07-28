import { describe, expect, it } from "vitest";

import { parseWsMessage } from "./ws-messages";

describe("parseWsMessage", () => {
  it("parses pings", () => {
    expect(parseWsMessage(JSON.stringify({ type: "ping" }))).toEqual({ kind: "ping" });
  });

  it("treats a stage frame with no status as a start", () => {
    const msg = parseWsMessage(
      JSON.stringify({ stage_number: 3, total_stages: 9, message: "Checking your order..." })
    );
    expect(msg).toMatchObject({
      kind: "stage",
      stageNumber: 3,
      totalStages: 9,
      message: "Checking your order...",
      status: "start",
    });
  });

  it("carries the measured duration on a stage done frame", () => {
    const msg = parseWsMessage(
      JSON.stringify({
        type: "stage",
        status: "done",
        stage_number: 4,
        total_stages: 9,
        message: "Finding the right policy...",
        duration_ms: 287.4,
        turn_id: "turn-1",
      })
    );
    expect(msg).toMatchObject({
      kind: "stage",
      stageNumber: 4,
      status: "done",
      durationMs: 287.4,
      turnId: "turn-1",
    });
  });

  it("parses the deferred audio frame", () => {
    const msg = parseWsMessage(
      JSON.stringify({
        type: "audio",
        response_audio_base64: "UklGRg==",
        turn_id: "turn-1",
      })
    );
    expect(msg).toEqual({
      kind: "audio",
      audioBase64: "UklGRg==",
      turnId: "turn-1",
    });
  });

  it("ignores an audio frame with no payload", () => {
    // Guards the hook against claiming the TTS race with nothing to play.
    expect(parseWsMessage(JSON.stringify({ type: "audio" }))).toEqual({ kind: "unknown" });
  });

  it("parses the terminal done frame with trace and total duration", () => {
    const msg = parseWsMessage(
      JSON.stringify({
        type: "done",
        is_complete: true,
        turn_id: "turn-1",
        ticket_id: "abc-123",
        ticket_number: "TKT-9QXM2",
        ticket_created: true,
        agent_trace: [{ agent_name: "Voice Intake", stage_number: 1 }],
        total_duration_ms: 4821.5,
      })
    );
    expect(msg).toMatchObject({
      kind: "done",
      ticketId: "abc-123",
      ticketNumber: "TKT-9QXM2",
      ticketCreated: true,
      totalDurationMs: 4821.5,
    });
    if (msg.kind === "done") {
      expect(msg.agentTrace).toHaveLength(1);
    }
  });

  it("defaults a done frame's missing fields rather than throwing", () => {
    const msg = parseWsMessage(JSON.stringify({ type: "done" }));
    expect(msg).toMatchObject({
      kind: "done",
      ticketId: "",
      ticketCreated: false,
      agentTrace: [],
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
