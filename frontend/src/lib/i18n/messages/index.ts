/**
 * Assembles all message catalogs into a single lookup.
 * Hinglish deliberately maps to "en" — Hinglish speakers read Latin-script English fine;
 * a separate Hinglish catalog would be identical and would drift out of sync.
 */
import en, { type Messages } from "./en";
import hi from "./hi";
import ml from "./ml";
import ta from "./ta";
import te from "./te";
import kn from "./kn";
import bn from "./bn";
import mr from "./mr";

export type Locale = "en" | "hi" | "ml" | "ta" | "te" | "kn" | "bn" | "mr";

export const MESSAGES: Record<Locale, Messages> = {
  en,
  hi,
  ml,
  ta,
  te,
  kn,
  bn,
  mr,
};

export { en };
export type { Messages };
