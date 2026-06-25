/**
 * CommerceMind VoiceCare AI — Shared Frontend Constants
 */

export const LANGUAGES = [
  "Hindi", "English", "Malayalam", "Tamil", "Telugu",
  "Kannada", "Bengali", "Marathi", "Hinglish",
] as const;

export type Language = (typeof LANGUAGES)[number];

// Maps display language names to BCP-47 locale codes for Web Speech API
export const LANG_TO_BCP47: Record<string, string> = {
  Hindi: "hi-IN",
  English: "en-IN",
  Malayalam: "ml-IN",
  Tamil: "ta-IN",
  Telugu: "te-IN",
  Kannada: "kn-IN",
  Bengali: "bn-IN",
  Marathi: "mr-IN",
  Hinglish: "hi-IN",
};

// Maps display language names to i18n locale codes used by the UI catalog.
// Hinglish maps to "en" — Hinglish readers use Latin-script English labels.
export type Locale = "en" | "hi" | "ml" | "ta" | "te" | "kn" | "bn" | "mr";

export const LANG_TO_LOCALE: Record<string, Locale> = {
  Hindi: "hi",
  English: "en",
  Malayalam: "ml",
  Tamil: "ta",
  Telugu: "te",
  Kannada: "kn",
  Bengali: "bn",
  Marathi: "mr",
  Hinglish: "en",
};
