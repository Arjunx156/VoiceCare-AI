"use client";

import { useVoiceInteraction } from "@/hooks/useVoiceInteraction";
import { I18nProvider } from "@/lib/i18n/I18nProvider";
import { LANG_TO_LOCALE } from "@/lib/constants";
import VoiceView from "@/components/VoiceView";

export default function VoicePage() {
  const voiceState = useVoiceInteraction();
  const locale = LANG_TO_LOCALE[voiceState.selectedLanguage] ?? "hi";

  return (
    <I18nProvider locale={locale}>
      <VoiceView {...voiceState} />
    </I18nProvider>
  );
}
