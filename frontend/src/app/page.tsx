"use client";

/**
 * CommerceMind VoiceCare AI — Voice Screen v2
 * Design brief: bg-base, eyebrow → headline, coral orb, pill record button,
 * language trust-bar, no glassmorphism.
 */

import { useState, useRef, useCallback, useEffect, Suspense } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import StatusStream from "@/components/StatusStream";
import { sendVoiceQuery, type VoiceQueryResponse } from "@/lib/api";

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

const LANGUAGES = [
  "Hindi", "English", "Malayalam", "Tamil", "Telugu",
  "Kannada", "Bengali", "Marathi", "Hinglish",
];

const LANG_TO_BCP47: Record<string, string> = {
  Hindi: "hi-IN", English: "en-IN", Malayalam: "ml-IN", Tamil: "ta-IN",
  Telugu: "te-IN", Kannada: "kn-IN", Bengali: "bn-IN", Marathi: "mr-IN",
  Hinglish: "hi-IN",
};

// Staggered fade-up variants
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1], delay: i * 0.07 },
  }),
};

// OrbState label eyebrow
function orbEyebrow(isListening: boolean, isProcessing: boolean, isComplete: boolean) {
  if (isListening)  return "LISTENING";
  if (isProcessing) return "THINKING";
  if (isComplete)   return "DONE";
  return "VOICE SUPPORT";
}

export default function VoicePage() {
  const [isListening, setIsListening]     = useState(false);
  const [isProcessing, setIsProcessing]   = useState(false);
  const [audioLevel, setAudioLevel]       = useState(0);
  const [currentStage, setCurrentStage]   = useState(0);
  const [isComplete, setIsComplete]       = useState(false);
  const [response, setResponse]           = useState<VoiceQueryResponse | null>(null);
  const [error, setError]                 = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState("Hindi");
  const [sessionId, setSessionId]         = useState<string | null>(null);
  const [textInput, setTextInput]         = useState("");
  const [showTextMode, setShowTextMode]   = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [bhashiniWarning, setBhashiniWarning] = useState(false);

  const mediaRecorderRef  = useRef<MediaRecorder | null>(null);
  const audioChunksRef    = useRef<Blob[]>([]);
  const analyserRef       = useRef<AnalyserNode | null>(null);
  const animFrameRef      = useRef<number>(0);
  const streamRef         = useRef<MediaStream | null>(null);
  const recognitionRef    = useRef<any>(null);
  const transcriptAccRef  = useRef<string>("");

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  const monitorAudio = useCallback((stream: MediaStream) => {
    const audioCtx = new AudioContext();
    const source   = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;
    const data = new Uint8Array(analyser.frequencyBinCount);
    const update = () => {
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length;
      setAudioLevel(avg / 255);
      animFrameRef.current = requestAnimationFrame(update);
    };
    update();
  }, []);

  const startSpeechRecognition = useCallback((language: string) => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    transcriptAccRef.current = "";
    setLiveTranscript("");
    const recognition = new SR();
    recognition.lang = LANG_TO_BCP47[language] || "hi-IN";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event: any) => {
      let interim = "", final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += t;
        else interim += t;
      }
      if (final) transcriptAccRef.current += " " + final;
      setLiveTranscript((transcriptAccRef.current + interim).trim());
    };
    recognition.onerror = () => {};
    recognitionRef.current = recognition;
    recognition.start();
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setResponse(null);
      setIsComplete(false);
      setCurrentStage(0);
      setBhashiniWarning(false);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      monitorAudio(stream);
      startSpeechRecognition(selectedLanguage);

      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current   = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null; }
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        stream.getTracks().forEach((t) => t.stop());
        setAudioLevel(0);
        setIsListening(false);
        const capturedTranscript = transcriptAccRef.current.trim();
        setLiveTranscript("");
        const blob   = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(",")[1];
          processQuery({ audio_base64: base64, text: capturedTranscript || undefined });
        };
        reader.readAsDataURL(blob);
      };

      mediaRecorder.start(100);
      setIsListening(true);
    } catch {
      setError("Microphone access denied. Please allow microphone access.");
    }
  }, [monitorAudio, startSpeechRecognition, selectedLanguage]); // eslint-disable-line

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const processQuery = useCallback(
    async (overrides: { text?: string; audio_base64?: string } = {}) => {
      setIsProcessing(true);
      setCurrentStage(1);
      const stageInterval = setInterval(() => {
        setCurrentStage((prev) => {
          if (prev >= 9) { clearInterval(stageInterval); return 9; }
          return prev + 1;
        });
      }, 800);
      try {
        const result = await sendVoiceQuery({
          text: overrides.text,
          audio_base64: overrides.audio_base64,
          language: selectedLanguage,
          session_id: sessionId || undefined,
        });
        clearInterval(stageInterval);
        setCurrentStage(9);
        setResponse(result);
        setSessionId(result.session_id);
        setIsComplete(true);
        if (result.response_audio_base64) playAudioResponse(result.response_audio_base64);
      } catch (err: any) {
        clearInterval(stageInterval);
        const msg: string = err.message || "Something went wrong. Please try again.";
        if (msg.toLowerCase().includes("voice recognition") || msg.toLowerCase().includes("temporarily unavailable")) {
          setBhashiniWarning(true);
          setShowTextMode(true);
          setError(null);
        } else {
          setError(msg);
        }
      } finally {
        setIsProcessing(false);
      }
    },
    [selectedLanguage, sessionId] // eslint-disable-line
  );

  const playAudioResponse = (base64Audio: string) => {
    const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
    audio.play().catch(() => {});
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || isProcessing) return;
    processQuery({ text: textInput.trim() });
    setTextInput("");
  };

  const eyebrow = orbEyebrow(isListening, isProcessing, isComplete);

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
      {/* Header */}
      <header
        style={{
          width: "100%",
          maxWidth: 560,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "20px 24px 0",
        }}
      >
        <div>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", color: "var(--accent)", textTransform: "uppercase" }}>
            CommerceMind
          </span>
          <h1 style={{ fontSize: 18, fontWeight: 800, color: "var(--text-primary)", marginTop: 2 }}>
            VoiceCare AI
          </h1>
        </div>
        <Link
          href="/dashboard"
          style={{
            padding: "8px 18px",
            borderRadius: 999,
            fontSize: 12,
            fontWeight: 600,
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
            background: "transparent",
            textDecoration: "none",
            transition: "border-color 150ms, color 150ms",
          }}
        >
          Admin →
        </Link>
      </header>

      {/* Bhashini Warning Banner */}
      <AnimatePresence>
        {bhashiniWarning && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            style={{ width: "100%", maxWidth: 560, padding: "12px 24px 0" }}
          >
            <div
              style={{
                borderRadius: 12,
                padding: "12px 16px",
                fontSize: 13,
                display: "flex",
                alignItems: "flex-start",
                gap: 10,
                background: "rgba(212, 160, 23, 0.10)",
                border: "1px solid rgba(212, 160, 23, 0.3)",
                color: "#D4A017",
              }}
            >
              <span style={{ fontSize: "1rem", flexShrink: 0 }}>⚠</span>
              <span style={{ flex: 1, lineHeight: 1.5 }}>
                <strong>Voice recognition temporarily unavailable.</strong> Type your query below — everything else works perfectly.
              </span>
              <button
                onClick={() => setBhashiniWarning(false)}
                style={{ opacity: 0.5, flexShrink: 0, background: "none", border: "none", color: "inherit", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Orb section */}
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
        {/* Eyebrow → Headline staggered fade-up */}
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
          {isListening
            ? "I'm listening…"
            : isProcessing
            ? "Working on it…"
            : isComplete
            ? "Here's what I found"
            : "Speak your issue"}
        </motion.h2>

        {/* Orb */}
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

        {/* Live transcript */}
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

        {/* Status Stream */}
        <div style={{ width: "100%", marginTop: 16 }}>
          <StatusStream currentStage={currentStage} isComplete={isComplete} />
        </div>

        {/* Response */}
        <AnimatePresence>
          {response && isComplete && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="panel"
              style={{ width: "100%", marginTop: 16, padding: "20px 24px" }}
            >
              {/* Eyebrow + status */}
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <span className="eyebrow" style={{ marginBottom: 0 }}>
                  {response.intent.replace(/_/g, " ")}
                </span>
                <span
                  style={{
                    marginLeft: "auto",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 10px",
                    borderRadius: 999,
                    background: response.is_escalated ? "rgba(229,57,53,0.12)" : "rgba(76,175,115,0.12)",
                    color: response.is_escalated ? "var(--status-high)" : "var(--status-low)",
                  }}
                >
                  {response.is_escalated ? "Escalated" : "Resolved"}
                </span>
              </div>

              {/* Divider */}
              <div className="divider" style={{ marginBottom: 14 }} />

              <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--text-primary)" }}>
                {response.response_text}
              </p>

              {response.policy_reference && (
                <p style={{ fontSize: 12, marginTop: 12, color: "var(--text-secondary)", fontStyle: "italic" }}>
                  📋 {response.policy_reference.substring(0, 120)}…
                </p>
              )}

              <div
                style={{
                  display: "flex",
                  gap: 16,
                  marginTop: 14,
                  fontSize: 12,
                  color: "var(--text-muted)",
                }}
              >
                <span>Ticket {response.ticket_id?.substring(0, 8)}…</span>
                <span>Confidence {(response.confidence_score * 100).toFixed(0)}%</span>
                <span>{response.sentiment}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
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
            <p style={{ fontSize: 13, color: "var(--error)" }}>{error}</p>
          </motion.div>
        )}
      </section>

      {/* Controls footer */}
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
        {/* Language trust bar */}
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

        {/* Record / Text Input */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 16, width: "100%" }}>
          {!showTextMode ? (
            <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
              {/* Active recording ring */}
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
                aria-label={isListening ? "Stop recording" : "Start recording"}
              >
                {isListening ? (
                  // Stop icon
                  <svg width="18" height="18" fill="white" viewBox="0 0 24 24">
                    <rect x="6" y="6" width="12" height="12" rx="2" />
                  </svg>
                ) : (
                  // Mic icon
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
                placeholder="Type your query in any language…"
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
                Send
              </button>
            </form>
          )}
        </div>

        {/* Voice / text toggle */}
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
          {showTextMode ? "Switch to Voice" : "Switch to Text"}
        </button>
      </footer>
    </main>
  );
}
