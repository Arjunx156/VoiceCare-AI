/**
 * CommerceMind VoiceCare AI — Shared Frontend Constants
 */

export const LANGUAGES = [
  "Hindi", "English", "Malayalam", "Tamil", "Telugu",
  "Kannada", "Bengali", "Marathi", "Hinglish",
] as const;

export type Language = (typeof LANGUAGES)[number];

// Each supported language in its own script — shown on the voice hero so a
// customer recognizes their language instantly, before reading any English.
export const NATIVE_LANGUAGE_NAMES: Record<Language, string> = {
  Hindi: "हिन्दी",
  English: "English",
  Malayalam: "മലയാളം",
  Tamil: "தமிழ்",
  Telugu: "తెలుగు",
  Kannada: "ಕನ್ನಡ",
  Bengali: "বাংলা",
  Marathi: "मराठी",
  Hinglish: "Hinglish",
};

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
