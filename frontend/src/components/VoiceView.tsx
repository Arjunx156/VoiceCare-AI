"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
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

export default function VoiceView(props: VoiceState) {
  const {
    isListening,
    isProcessing,
    isComplete,
    audioLevel,
    currentStage,
    response,
    turns,
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
    startNewConversation,
    phone,
    setPhone,
  } = props;

  const { t } = useI18n();

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

  return (
    <main
      style={{
        minHeight: "100vh",
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
          style={{ textAlign: "center", marginBottom: 8 }}
        >
          <span className="eyebrow" style={{ textAlign: "center", display: "block" }}>
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
            lineHeight: 1.15,
            marginBottom: 32,
          }}
        >
          {headline}
        </motion.h2>

        <motion.div
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          style={{ width: "100%", height: 280 }}
        >
          <Suspense fallback={<div style={{ width: "100%", height: "100%" }} />}>
            <VoiceOrb
              isListening={isListening}
              isProcessing={isProcessing}
              audioLevel={audioLevel}
            />
          </Suspense>
        </motion.div>

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

        <ConversationThread turns={turns} />

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
        startRecording={startRecording}
        stopRecording={stopRecording}
        textInput={textInput}
        setTextInput={setTextInput}
        handleTextSubmit={handleTextSubmit}
        setBhashiniWarning={setBhashiniWarning}
        startNewConversation={startNewConversation}
        hasResponse={!!response}
        phone={phone}
        setPhone={setPhone}
      />
    </main>
  );
}
