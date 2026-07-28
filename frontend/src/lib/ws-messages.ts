/**
 * Typed WebSocket message contract for /api/voice/ws/{session_id}.
 * The server sends six frame shapes; parseWsMessage narrows raw JSON into
 * this union so the voice hook never touches untyped `data.*` fields.
 *
 * Frame order for one turn:
 *   stage(start 1) → stage(done 1) → … → stage(done 7)
 *   → response          (the answer — displayed immediately)
 *   → stage(start 8) … → audio      (Bhashini speech, if it succeeded)
 *   → stage(start 9) … → done       (terminal; carries the full agent trace)
 *
 * Stages 8 (speech synthesis) and 9 (ticket persistence) run after the answer
 * is already on screen, so their frames arrive last.
 */

import type { AgentTraceStep, VoiceQueryResponse } from "./api";

export type StageStatus = "start" | "done";

export type WsMessage =
  | { kind: "ping" }
  | {
      kind: "stage";
      stageNumber: number;
      totalStages: number;
      message: string;
      status: StageStatus;
      durationMs?: number;
      turnId?: string;
    }
  | { kind: "response"; response: VoiceQueryResponse; turnId?: string }
  | { kind: "audio"; audioBase64: string; turnId?: string }
  | {
      kind: "done";
      turnId?: string;
      ticketId: string;
      ticketNumber?: string;
      ticketCreated: boolean;
      agentTrace: AgentTraceStep[];
      totalDurationMs?: number;
    }
  | { kind: "error"; code: string; detail: unknown; retryAfter?: number }
  | { kind: "unknown" };

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function optionalNumber(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined;
}

export function parseWsMessage(raw: string): WsMessage {
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return { kind: "unknown" };
  }
  if (typeof data !== "object" || data === null) return { kind: "unknown" };

  const msg = data as Record<string, unknown>;

  if (msg.type === "ping") return { kind: "ping" };

  if (msg.type === "response") {
    return {
      kind: "response",
      response: msg as unknown as VoiceQueryResponse,
      turnId: optionalString(msg.turn_id),
    };
  }

  if (msg.type === "audio" && typeof msg.response_audio_base64 === "string") {
    return {
      kind: "audio",
      audioBase64: msg.response_audio_base64,
      turnId: optionalString(msg.turn_id),
    };
  }

  if (msg.type === "done") {
    return {
      kind: "done",
      turnId: optionalString(msg.turn_id),
      ticketId: typeof msg.ticket_id === "string" ? msg.ticket_id : "",
      ticketNumber: optionalString(msg.ticket_number),
      ticketCreated: msg.ticket_created === true,
      agentTrace: Array.isArray(msg.agent_trace)
        ? (msg.agent_trace as AgentTraceStep[])
        : [],
      totalDurationMs: optionalNumber(msg.total_duration_ms),
    };
  }

  if (typeof msg.stage_number === "number") {
    return {
      kind: "stage",
      stageNumber: msg.stage_number,
      totalStages: typeof msg.total_stages === "number" ? msg.total_stages : 9,
      message: typeof msg.message === "string" ? msg.message : "",
      // Defaults to "start" so a frame from an older backend, which had no
      // status field, still reads as "this stage began".
      status: msg.status === "done" ? "done" : "start",
      durationMs: optionalNumber(msg.duration_ms),
      turnId: optionalString(msg.turn_id),
    };
  }

  if (typeof msg.error === "string") {
    return {
      kind: "error",
      code: msg.error,
      detail: msg.detail,
      retryAfter: optionalNumber(msg.retry_after),
    };
  }

  return { kind: "unknown" };
}
