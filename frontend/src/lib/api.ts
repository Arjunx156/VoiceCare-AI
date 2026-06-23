/**
 * CommerceMind VoiceCare AI — API Client
 * Handles all communication with the FastAPI backend.
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface VoiceQueryRequest {
  text?: string;
  audio_base64?: string;
  language?: string;
  phone?: string;
  order_id?: string;
  session_id?: string;
}

export interface VoiceQueryResponse {
  session_id: string;
  ticket_id: string;
  response_text: string;
  response_audio_base64?: string;
  language: string;
  intent: string;
  sentiment: string;
  priority: string;
  recommended_action: string;
  policy_reference?: string;
  confidence_score: number;
  is_escalated: boolean;
  escalation_reason?: string;
  agent_trace: AgentTraceStep[];
}

export interface AgentTraceStep {
  agent_name: string;
  stage_number: number;
  input_summary: string;
  output_summary: string;
  decision?: string;
  reasoning?: string;
  duration_ms?: number;
  timestamp: string;
}

export interface TicketSummary {
  ticket_id: string;
  user_name: string;
  phone: string;
  ticket_type: string;
  priority: string;
  status: string;
  language: string;
  sentiment?: string;
  summary?: string;
  created_at: string;
  resolved_at?: string;
}

export interface TicketDetail extends TicketSummary {
  escalated_at?: string;
  order_id?: string;
  order_status?: string;
  order_amount?: number;
  order_date?: string;
  recommended_action?: string;
  policy_reference?: string;
  response_text?: string;
  internal_note?: string;
  confidence_score?: number;
  agent_trace: AgentTraceStep[];
  messages: MessageItem[];
}

export interface MessageItem {
  message_id: string;
  sender_type: string;
  message_text: string;
  language: string;
  timestamp: string;
}

export interface AnalyticsOverview {
  total_tickets: number;
  open_tickets: number;
  escalated_tickets: number;
  resolved_tickets: number;
  avg_resolution_time_minutes?: number;
  tickets_by_language: Record<string, number>;
  tickets_by_category: Record<string, number>;
  tickets_by_priority: Record<string, number>;
  tickets_by_sentiment: Record<string, number>;
  tickets_over_time: { date: string; count: number }[];
  resolution_rate: number;
  escalation_rate: number;
}

export interface HandoffNote {
  ticket_id: string;
  customer_name: string;
  customer_phone: string;
  language: string;
  issue_summary: string;
  sentiment: string;
  priority: string;
  order_details?: string;
  ai_attempted_resolution: string;
  policy_referenced?: string;
  escalation_reason: string;
  recommended_next_steps: string;
  conversation_history: { sender: string; text: string; time: string }[];
  generated_at: string;
}

// ---- API Functions ----

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }
  return res.json();
}

export async function sendVoiceQuery(
  request: VoiceQueryRequest
): Promise<VoiceQueryResponse> {
  return apiFetch<VoiceQueryResponse>("/api/voice/query", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getTickets(params?: {
  status?: string;
  priority?: string;
  language?: string;
}): Promise<TicketSummary[]> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.priority) query.set("priority", params.priority);
  if (params?.language) query.set("language", params.language);
  const qs = query.toString();
  return apiFetch<TicketSummary[]>(`/api/tickets/${qs ? `?${qs}` : ""}`);
}

export async function getEscalations(): Promise<TicketSummary[]> {
  return apiFetch<TicketSummary[]>("/api/tickets/escalations");
}

export async function getTicketDetail(ticketId: string): Promise<TicketDetail> {
  return apiFetch<TicketDetail>(`/api/tickets/${ticketId}`);
}

export async function getAnalytics(): Promise<AnalyticsOverview> {
  return apiFetch<AnalyticsOverview>("/api/tickets/analytics");
}

export async function getHandoffNote(ticketId: string): Promise<HandoffNote> {
  return apiFetch<HandoffNote>(`/api/tickets/${ticketId}/handoff`);
}

export function createWebSocket(sessionId: string): WebSocket {
  const wsUrl = BACKEND_URL.replace("http", "ws");
  return new WebSocket(`${wsUrl}/api/voice/ws/${sessionId}`);
}
