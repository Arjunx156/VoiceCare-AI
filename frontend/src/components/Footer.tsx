"use client";

import { motion } from "framer-motion";
import { LANGUAGES } from "@/lib/constants";
import { useI18n } from "@/lib/i18n/I18nProvider";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as [number, number, number, number], delay: i * 0.07 },
  }),
};

interface FooterProps {
  selectedLanguage: string;
  setSelectedLanguage: (lang: string) => void;
  showTextMode: boolean;
  setShowTextMode: (show: boolean) => void;
  isListening: boolean;
  isProcessing: boolean;
  startRecording: () => void;
  stopRecording: () => void;
  textInput: string;
  setTextInput: (text: string) => void;
  handleTextSubmit: (e: React.FormEvent) => void;
  setBhashiniWarning: (show: boolean) => void;
  startNewConversation: () => void;
  hasResponse: boolean;
  phone: string;
  setPhone: (v: string) => void;
}

export default function Footer({
  selectedLanguage,
  setSelectedLanguage,
  showTextMode,
  setShowTextMode,
  isListening,
  isProcessing,
  startRecording,
  stopRecording,
  textInput,
  setTextInput,
  handleTextSubmit,
  setBhashiniWarning,
  startNewConversation,
  hasResponse,
  phone,
  setPhone,
}: FooterProps) {
  const { t } = useI18n();

  return (
    <footer
      style={{
        width: "100%",
        maxWidth: 560,
        padding: "0 24px 48px",
        display: "flex",
        flexDirection: "column",
        gap: 20,
        alignItems: "center",
      }}
    >
      <motion.div
        custom={3}
        variants={fadeUp}
        initial="hidden"
        animate="show"
        style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 6 }}
      >
        {LANGUAGES.map((lang) => (
          <button
            key={lang}
            onClick={() => setSelectedLanguage(lang)}
            className={`lang-pill${selectedLanguage === lang ? " active" : ""}`}
          >
            {lang}
          </button>
        ))}
      </motion.div>
      {/* Optional phone — lets the backend look up a real order on turn 1 */}
      {!hasResponse && (
        <motion.div
          custom={3.5}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          style={{ width: "100%", maxWidth: 280 }}
        >
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="Phone number (optional)"
            disabled={isListening || isProcessing}
            style={{
              width: "100%",
              padding: "8px 16px",
              borderRadius: 999,
              fontSize: 13,
              outline: "none",
              background: "var(--bg-panel)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-secondary)",
              fontFamily: "var(--font-sans)",
              textAlign: "center",
              opacity: isListening || isProcessing ? 0.4 : 1,
              boxSizing: "border-box",
            }}
          />
        </motion.div>
      )}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 16, width: "100%" }}>
        {!showTextMode ? (
          <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
            {isListening && <span className="record-ring" />}
            <motion.button
              whileHover={!isProcessing ? { scale: 1.02 } : {}}
              whileTap={!isProcessing ? { scale: 0.98 } : {}}
              onClick={isListening ? stopRecording : startRecording}
              disabled={isProcessing}
              className="btn-pill btn-pill-accent"
              style={{
                width: 64,
                height: 64,
                padding: 0,
                fontSize: 20,
                background: isListening ? "var(--error)" : "var(--accent)",
                opacity: isProcessing ? 0.4 : 1,
                cursor: isProcessing ? "not-allowed" : "pointer",
              }}
              aria-label={isListening ? t("footer.stopRecording") : t("footer.startRecording")}
            >
              {isListening ? (
                <svg width="18" height="18" fill="white" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : (
                <svg width="20" height="20" fill="white" viewBox="0 0 24 24">
                  <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round"/>
                  <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              )}
            </motion.button>
          </div>
        ) : (
          <form onSubmit={handleTextSubmit} style={{ flex: 1, display: "flex", gap: 8 }}>
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={t("footer.placeholder")}
              disabled={isProcessing}
              autoFocus
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: 999,
                fontSize: 14,
                outline: "none",
                background: "var(--bg-panel)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-sans)",
              }}
            />
            <button
              type="submit"
              disabled={isProcessing || !textInput.trim()}
              className="btn-pill btn-pill-accent"
              style={{ padding: "12px 20px" }}
            >
              {t("footer.send")}
            </button>
          </form>
        )}
      </div>
      <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
        <button
          onClick={() => { setShowTextMode(!showTextMode); setBhashiniWarning(false); }}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: 12,
            color: "var(--text-muted)",
            fontFamily: "var(--font-sans)",
            transition: "color 150ms",
          }}
        >
          {showTextMode ? t("footer.switchToVoice") : t("footer.switchToText")}
        </button>
        {hasResponse && (
          <button
            onClick={startNewConversation}
            disabled={isListening || isProcessing}
            style={{
              background: "none",
              border: "1px solid var(--border-subtle)",
              borderRadius: 999,
              cursor: isListening || isProcessing ? "not-allowed" : "pointer",
              fontSize: 12,
              color: "var(--text-secondary)",
              fontFamily: "var(--font-sans)",
              padding: "4px 12px",
              opacity: isListening || isProcessing ? 0.4 : 1,
              transition: "color 150ms, border-color 150ms",
            }}
          >
            {t("footer.newConversation")}
          </button>
        )}
      </div>
    </footer>
  );
}
