"use client";

import { Suspense, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { LANGUAGES, NATIVE_LANGUAGE_NAMES } from "@/lib/constants";
import StatusStream from "@/components/StatusStream";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ConversationThread from "@/components/ConversationThread";
import BhashiniWarning from "@/components/BhashiniWarning";
import { useI18n } from "@/lib/i18n/I18nProvider";
import type { useVoiceInteraction } from "@/hooks/useVoiceInteraction";

const VoiceOrb = dynamic(() => import("@/components/VoiceOrb"), {
  ssr: false,
  loading: () => (
    <div className="w-full flex items-center justify-center" style={{ minHeight: "300px" }}>
      <div
        style={{
          width: 96, height: 96, borderRadius: "50%",
          background: "#FF5A2B",
          opacity: 0.3,
          animation: "orb-breathe 4s ease-in-out infinite",
        }}
      />
    </div>
  ),
});

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as [number, number, number, number], delay: i * 0.07 },
  }),
};

type VoiceState = ReturnType<typeof useVoiceInteraction>;

const NATIVE_NAMES = LANGUAGES.map((l) => NATIVE_LANGUAGE_NAMES[l]);
const ROTATE_MS = 2200;

/**
 * The product's identity in one detail: each supported language, shown in its
 * own script, rotating quietly under the idle headline. A customer recognizes
 * their language before reading a word of English. Decorative (aria-hidden) —
 * the language pills below are the real, accessible selector. Under reduced
 * motion the full list renders as a static line instead.
 */
function RotatingLanguageLine() {
  const reduced = useReducedMotion();
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (reduced) return;
    const id = setInterval(() => setIdx((i) => (i + 1) % NATIVE_NAMES.length), ROTATE_MS);
    return () => clearInterval(id);
  }, [reduced]);

  if (reduced) {
    return (
      <p
        aria-hidden="true"
        style={{
          fontSize: 14,
          fontWeight: 600,
          color: "var(--text-secondary)",
          textAlign: "center",
          lineHeight: 1.8,
        }}
      >
        {NATIVE_NAMES.join("  ·  ")}
      </p>
    );
  }

  return (
    <span
      aria-hidden="true"
      style={{
        display: "inline-flex",
        justifyContent: "center",
        minWidth: 120,
        height: 26,
        overflow: "hidden",
      }}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={idx}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
          style={{ fontSize: 17, fontWeight: 600, color: "var(--text-secondary)", lineHeight: "26px" }}
        >
          {NATIVE_NAMES[idx]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

export default function VoiceView(props: VoiceState) {
  const {
    isListening,
    isProcessing,
    isComplete,
    audioLevelRef,
    currentStage,
    response,
    turns,
    restoredTurns,
    errorCode,
    selectedLanguage,
    setSelectedLanguage,
    textInput,
    setTextInput,
    showTextMode,
    setShowTextMode,
    liveTranscript,
    bhashiniWarning,
    setBhashiniWarning,
    startRecording,
    stopRecording,
    handleTextSubmit,
    submitText,
    startNewConversation,
    phone,
    setPhone,
  } = props;

  const { t } = useI18n();

  // Secondary state cue beside the eyebrow (never the only cue — the eyebrow
  // and headline text change too). Semantic status colors, not the accent,
  // except "listening" which IS the brand moment.
  const stateDotColor = isListening
    ? "var(--accent)"
    : isProcessing
    ? "var(--status-medium)"
    : isComplete
    ? "var(--status-low)"
    : "var(--status-calm)";

  const eyebrow = isListening
    ? t("voice.eyebrow.listening")
    : isProcessing
    ? t("voice.eyebrow.thinking")
    : isComplete
    ? t("voice.eyebrow.done")
    : t("voice.eyebrow.idle");

  const headline = isListening
    ? t("voice.headline.listening")
    : isProcessing
    ? t("voice.headline.thinking")
    : isComplete
    ? t("voice.headline.done")
    : t("voice.headline.idle");

  // The rotating language line is a first-visit hero moment only: it steps
  // aside as soon as a conversation exists in any form.
  const showLanguageLine =
    !isListening && !isProcessing && !isComplete && turns.length === 0 && restoredTurns.length === 0;

  return (
    <main
      style={{
        // dvh, not vh: on mobile the browser chrome overlaps 100vh and the
        // bottom controls get clipped/cramped.
        minHeight: "100dvh",
        background: "var(--bg-base)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        position: "relative",
        zIndex: 1,
      }}
    >
      <Header />

      <AnimatePresence>
        {bhashiniWarning && (
          <BhashiniWarning onClose={() => setBhashiniWarning(false)} />
        )}
      </AnimatePresence>

      <section
        style={{
          flex: 1,
          width: "100%",
          maxWidth: 560,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 24px",
          gap: 0,
        }}
      >
        <motion.div
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            marginBottom: 8,
          }}
        >
          <span
            className="status-dot"
            aria-hidden="true"
            style={{ background: stateDotColor, transition: "background 300ms ease-out" }}
          />
          <span className="eyebrow" style={{ marginBottom: 0 }}>
            {eyebrow}
          </span>
        </motion.div>

        <motion.h2
          custom={1}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          style={{
            fontSize: "clamp(28px, 5vw, 44px)",
            fontWeight: 800,
            color: "var(--text-primary)",
            textAlign: "center",
            lineHeight: 1.08,
            letterSpacing: "-0.025em",
            maxWidth: "18ch",
            marginBottom: showLanguageLine ? 10 : 24,
          }}
        >
          {headline}
        </motion.h2>

        {showLanguageLine && (
          <motion.div
            custom={1.5}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            style={{ marginBottom: 12, textAlign: "center" }}
          >
            <RotatingLanguageLine />
            <span className="sr-only">
              Hindi, English, Malayalam, Tamil, Telugu, Kannada, Bengali, Marathi, Hinglish
            </span>
          </motion.div>
        )}

        {/* The orb + record button are ONE focal unit: the primary action
            lives where the eye already is, not in a distant footer. */}
        <motion.div
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          style={{ width: "100%", height: 256 }}
        >
          <Suspense fallback={<div style={{ width: "100%", height: "100%" }} />}>
            <VoiceOrb
              isListening={isListening}
              isProcessing={isProcessing}
              audioLevelRef={audioLevelRef}
            />
          </Suspense>
        </motion.div>

        {!showTextMode && (
          <motion.div
            custom={2.2}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            style={{
              position: "relative",
              zIndex: 2,
              marginTop: -24,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {isListening && <span className="record-ring" />}
            <motion.button
              whileHover={!isProcessing ? { scale: 1.02 } : {}}
              whileTap={!isProcessing ? { scale: 0.98 } : {}}
              onClick={isListening ? stopRecording : startRecording}
              disabled={isProcessing}
              className="btn-pill btn-pill-accent"
              style={{
                width: 72,
                height: 72,
                padding: 0,
                fontSize: 20,
                background: isListening ? "var(--error)" : "var(--accent)",
                // Busy reads as "working" (spinner, slight dim) — not disabled-broken.
                opacity: isProcessing ? 0.75 : 1,
                cursor: isProcessing ? "not-allowed" : "pointer",
              }}
              aria-label={
                isProcessing
                  ? t("status.processing")
                  : isListening
                  ? t("footer.stopRecording")
                  : t("footer.startRecording")
              }
              aria-pressed={isListening}
            >
              {isProcessing ? (
                // Busy ring (white on accent) — reuses the global `spin`
                // keyframe; freezes under prefers-reduced-motion.
                <span
                  aria-hidden="true"
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: "50%",
                    border: "2.5px solid rgba(255,255,255,0.35)",
                    borderTopColor: "#fff",
                    animation: "spin 1s linear infinite",
                    display: "inline-block",
                  }}
                />
              ) : isListening ? (
                <svg width="18" height="18" fill="white" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : (
                <svg width="20" height="20" fill="white" viewBox="0 0 24 24">
                  <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
                  <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" strokeLinecap="round" />
                </svg>
              )}
            </motion.button>
          </motion.div>
        )}

        {/* One-tap starter queries — first-visit only, in the selected language */}
        {showLanguageLine && (
          <motion.div
            custom={2.5}
            variants={fadeUp}
            initial="hidden"
            animate="show"
            style={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: 8,
              marginTop: 18,
            }}
          >
            {(["voice.chip.order", "voice.chip.refund", "voice.chip.damaged"] as const).map(
              (key) => (
                <button
                  key={key}
                  type="button"
                  className="query-chip"
                  disabled={isListening || isProcessing}
                  onClick={() => submitText(t(key))}
                >
                  {t(key)}
                </button>
              ),
            )}
          </motion.div>
        )}

        <AnimatePresence>
          {isListening && liveTranscript && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{
                width: "100%",
                marginTop: 12,
                padding: "10px 16px",
                borderRadius: 12,
                fontSize: 13,
                color: "var(--text-secondary)",
                background: "var(--bg-panel)",
                border: "1px solid var(--border-subtle)",
                minHeight: "2.5rem",
                textAlign: "center",
              }}
            >
              {liveTranscript}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Stable live region: newly completed turns are announced politely */}
        <div aria-live="polite" style={{ width: "100%" }}>
          <ConversationThread turns={turns} restoredTurns={restoredTurns} />
        </div>

        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              style={{ width: "100%", marginTop: 16 }}
            >
              <StatusStream
                currentStage={currentStage}
                isComplete={isComplete}
                isProcessing={isProcessing}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {errorCode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            role="alert"
            className="panel"
            style={{
              width: "100%",
              marginTop: 16,
              padding: "16px 20px",
              borderColor: "rgba(229,57,53,0.35)",
              textAlign: "center",
            }}
          >
            <p style={{ fontSize: 13, color: "var(--error)" }}>{t(`error.${errorCode}`)}</p>
          </motion.div>
        )}
      </section>

      <Footer
        selectedLanguage={selectedLanguage}
        setSelectedLanguage={setSelectedLanguage}
        showTextMode={showTextMode}
        setShowTextMode={setShowTextMode}
        isListening={isListening}
        isProcessing={isProcessing}
        textInput={textInput}
        setTextInput={setTextInput}
        handleTextSubmit={handleTextSubmit}
        setBhashiniWarning={setBhashiniWarning}
        startNewConversation={startNewConversation}
        hasResponse={!!response || restoredTurns.length > 0}
        phone={phone}
        setPhone={setPhone}
      />
    </main>
  );
}
