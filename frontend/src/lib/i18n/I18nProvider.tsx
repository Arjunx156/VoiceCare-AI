"use client";

import { createContext, useContext, type ReactNode } from "react";
import { MESSAGES, en, type Locale, type Messages } from "./messages";

interface I18nContextValue {
  t: (key: keyof Messages) => string;
  locale: Locale;
}

const I18nContext = createContext<I18nContextValue>({
  t: (key) => en[key],
  locale: "hi",
});

export function I18nProvider({ locale, children }: { locale: Locale; children: ReactNode }) {
  const catalog = MESSAGES[locale] ?? en;

  function t(key: keyof Messages): string {
    return catalog[key] || en[key];
  }

  return <I18nContext.Provider value={{ t, locale }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
