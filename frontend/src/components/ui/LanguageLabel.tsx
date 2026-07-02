import { NATIVE_LANGUAGE_NAMES, type Language } from "@/lib/constants";

type Props = {
  language: string;
  style?: React.CSSProperties;
};

/**
 * A language shown in its own script (हिन्दी, தமிழ், …) — the voice hero's
 * approved identity detail carried into the operator console. Screen readers
 * and tooltips get the English name; unknown languages render as-is.
 */
export function LanguageLabel({ language, style }: Props) {
  const native = NATIVE_LANGUAGE_NAMES[language as Language];
  if (!native || native === language) {
    return <span style={style}>{language}</span>;
  }
  return (
    <span aria-label={language} title={language} style={style}>
      {native}
    </span>
  );
}
