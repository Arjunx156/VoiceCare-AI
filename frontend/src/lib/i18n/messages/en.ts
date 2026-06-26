/**
 * English — canonical message catalog.
 * The shape of this object defines `Messages` / `MessageKey`; every other
 * catalog is typed against it, so a missing key is a TypeScript build error.
 */

const en = {
  // Voice page — eyebrow label above the headline
  "voice.eyebrow.listening": "LISTENING",
  "voice.eyebrow.thinking": "THINKING",
  "voice.eyebrow.done": "DONE",
  "voice.eyebrow.idle": "VOICE SUPPORT",

  // Voice page — headline
  "voice.headline.listening": "I'm listening…",
  "voice.headline.thinking": "Working on it…",
  "voice.headline.done": "Here's what I found",
  "voice.headline.idle": "Speak your issue",

  // Footer controls
  "footer.startRecording": "Start recording",
  "footer.stopRecording": "Stop recording",
  "footer.send": "Send",
  "footer.placeholder": "Type your query in any language…",
  "footer.switchToVoice": "Switch to Voice",
  "footer.switchToText": "Switch to Text",
  "footer.newConversation": "New conversation",

  // Status stream
  "status.processing": "PROCESSING",
  "status.complete": "COMPLETE",
  "status.stage1": "Receiving audio",
  "status.stage2": "Understanding intent",
  "status.stage3": "Looking up order",
  "status.stage4": "Retrieving policy",
  "status.stage5": "Determining resolution",
  "status.stage6": "Checking escalation",
  "status.stage7": "Composing response",
  "status.stage8": "Converting to speech",
  "status.stage9": "Creating ticket",

  // Response panel
  "response.escalated": "Escalated",
  "response.resolved": "Resolved",
  "response.ticket": "Ticket",
  "response.confidence": "Confidence",

  // Bhashini warning banner
  "warning.title": "Voice recognition temporarily unavailable.",
  "warning.body": "Type your query below — everything else works perfectly.",

  // Error messages (keyed by stable error codes set in useVoiceInteraction)
  "error.micDenied": "Microphone access denied. Please allow microphone access.",
  "error.connection": "Connection error. Please try again.",
  "error.connectionLost": "Connection lost after multiple retries. Please try again.",
  "error.generic": "Something went wrong. Please try again.",
} as const;

export type MessageKey = keyof typeof en;
export type Messages = Record<MessageKey, string>;

export default en;
