/**
 * Typed WebSocket message contract for /api/voice/ws/{session_id}.
 * The server sends four frame shapes; parseWsMessage narrows raw JSON into
 * this union so the voice hook never touches untyped `data.*` fields.
 */

import type { VoiceQueryResponse } from "./api";

export type WsMessage =
  | { kind: "ping" }
  | { kind: "stage"; stageNumber: number; totalStages: number; message: string }
  | { kind: "response"; response: VoiceQueryResponse }
  | { kind: "error"; code: string; detail: unknown; retryAfter?: number }
  | { kind: "unknown" };

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
    return { kind: "response", response: msg as unknown as VoiceQueryResponse };
  }

  if (typeof msg.stage_number === "number") {
    return {
      kind: "stage",
      stageNumber: msg.stage_number,
      totalStages: typeof msg.total_stages === "number" ? msg.total_stages : 9,
      message: typeof msg.message === "string" ? msg.message : "",
    };
  }

  if (typeof msg.error === "string") {
    return {
      kind: "error",
      code: msg.error,
      detail: msg.detail,
      retryAfter: typeof msg.retry_after === "number" ? msg.retry_after : undefined,
    };
  }

  return { kind: "unknown" };
}
