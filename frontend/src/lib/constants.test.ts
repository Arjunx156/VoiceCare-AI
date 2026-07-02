import { describe, expect, it } from "vitest";

import { LANGUAGES, NATIVE_LANGUAGE_NAMES, LANG_TO_BCP47, LANG_TO_LOCALE } from "./constants";

describe("language constants", () => {
  it("every language has a non-empty native-script name", () => {
    for (const lang of LANGUAGES) {
      expect(NATIVE_LANGUAGE_NAMES[lang]?.trim().length).toBeGreaterThan(0);
    }
  });

  it("every language maps to a BCP-47 code and a UI locale", () => {
    for (const lang of LANGUAGES) {
      expect(LANG_TO_BCP47[lang]).toMatch(/^[a-z]{2}-[A-Z]{2}$/);
      expect(LANG_TO_LOCALE[lang]).toBeTruthy();
    }
  });
});
