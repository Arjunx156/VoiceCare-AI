"use client";

/**
 * CommerceMind VoiceCare AI — Main Voice Interface Page
 * Customer-facing page with voice orb, recording, and response playback.
 */

import { useState, useRef, useCallback, useEffect, Suspense } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import StatusStream from "@/components/StatusStream";
import { sendVoiceQuery, type VoiceQueryResponse } from "@/lib/api";

// Dynamic import for the 3D orb (SSR disabled)
const VoiceOrb = dynamic(() => import("@/components/VoiceOrb"), {
  ssr: false,
  loading: () => (
    <div className="w-full flex items-center justify-center" style={{ minHeight: "300px" }}>
      <div className="w-24 h-24 rounded-full animate-pulse" style={{ background: "var(--primary)" }} />
    </div>
  ),
});

const LANGUAGES = [
  "Hindi", "English", "Malayalam", "Tamil", "Telugu",
  "Kannada", "Bengali", "Marathi", "Hinglish",
];

export default function VoicePage() {
  // State
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [response, setResponse] = useState<VoiceQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState("Hindi");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [textInput, setTextInput] = useState("");
  const [showTextMode, setShowTextMode] = useState(false);

  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Audio level monitoring
  const monitorAudio = useCallback((stream: MediaStream) => {
    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const update = () => {
      analyser.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(avg / 255);
      animFrameRef.current = requestAnimationFrame(update);
    };
    update();
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setResponse(null);
      setIsComplete(false);
      setCurrentStage(0);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      monitorAudio(stream);

      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // Stop audio monitoring
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        stream.getTracks().forEach((t) => t.stop());
        setAudioLevel(0);
        setIsListening(false);

        // Convert to base64
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(",")[1];
          processQuery({ audio_base64: base64 });
        };
        reader.readAsDataURL(blob);
      };

      mediaRecorder.start(100);
      setIsListening(true);
    } catch (err) {
      setError("Microphone access denied. Please allow microphone access.");
    }
  }, [monitorAudio]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  // Process query (text or audio)
  const processQuery = useCallback(
    async (overrides: { text?: string; audio_base64?: string } = {}) => {
      setIsProcessing(true);
      setCurrentStage(1);

      // Simulate stage progression for UX
      const stageInterval = setInterval(() => {
        setCurrentStage((prev) => {
          if (prev >= 9) {
            clearInterval(stageInterval);
            return 9;
          }
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

        // Play audio response if available
        if (result.response_audio_base64) {
          playAudioResponse(result.response_audio_base64);
        }
      } catch (err: any) {
        clearInterval(stageInterval);
        setError(err.message || "Something went wrong. Please try again.");
      } finally {
        setIsProcessing(false);
      }
    },
    [selectedLanguage, sessionId]
  );

  // Play TTS audio
  const playAudioResponse = (base64Audio: string) => {
    const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
    audio.play().catch(() => {});
  };

  // Handle text submit
  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || isProcessing) return;
    processQuery({ text: textInput.trim() });
    setTextInput("");
  };

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-between relative"
      style={{ zIndex: 1 }}
    >
      {/* Header */}
      <header className="w-full flex items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            <span style={{ color: "var(--primary-light)" }}>VoiceCare</span> AI
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Speak Your Language. Get Resolved Instantly.
          </p>
        </div>
        <Link
          href="/dashboard"
          className="px-4 py-2 text-sm rounded-lg transition-all hover:opacity-80"
          style={{
            background: "var(--glass-bg)",
            border: "1px solid var(--glass-border)",
            color: "var(--text-secondary)",
          }}
        >
          Admin Dashboard →
        </Link>
      </header>

      {/* Voice Orb */}
      <section className="flex-1 w-full max-w-lg flex flex-col items-center justify-center px-4">
        <div className="w-full" style={{ height: "320px" }}>
          <Suspense fallback={<div className="w-full h-full" />}>
            <VoiceOrb
              isListening={isListening}
              isProcessing={isProcessing}
              audioLevel={audioLevel}
            />
          </Suspense>
        </div>

        {/* Status Stream */}
        <div className="w-full mt-4">
          <StatusStream
            currentStage={currentStage}
            isComplete={isComplete}
          />
        </div>

        {/* Response Display */}
        <AnimatePresence>
          {response && isComplete && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card w-full mt-4 p-5"
            >
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={`status-dot ${response.is_escalated ? "escalated" : "active"}`}
                />
                <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                  {response.is_escalated ? "Escalated to Human Agent" : "Resolved"}
                </span>
                <span className="ml-auto text-xs" style={{ color: "var(--text-muted)" }}>
                  {response.language} • {response.intent.replace(/_/g, " ")}
                </span>
              </div>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
                {response.response_text}
              </p>
              {response.policy_reference && (
                <p className="text-xs mt-3 italic" style={{ color: "var(--text-muted)" }}>
                  📋 Policy: {response.policy_reference.substring(0, 120)}...
                </p>
              )}
              <div className="flex items-center gap-4 mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
                <span>🎫 Ticket: {response.ticket_id?.substring(0, 8)}...</span>
                <span>📊 Confidence: {(response.confidence_score * 100).toFixed(0)}%</span>
                <span>😊 {response.sentiment}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card w-full mt-4 p-4 text-center"
            style={{ borderColor: "rgba(239, 68, 68, 0.3)" }}
          >
            <p className="text-sm" style={{ color: "var(--error)" }}>
              {error}
            </p>
          </motion.div>
        )}
      </section>

      {/* Controls */}
      <footer className="w-full max-w-lg px-4 pb-8 space-y-4">
        {/* Language Selector */}
        <div className="flex flex-wrap justify-center gap-2">
          {LANGUAGES.map((lang) => (
            <button
              key={lang}
              onClick={() => setSelectedLanguage(lang)}
              className="px-3 py-1.5 text-xs rounded-full transition-all"
              style={{
                background:
                  selectedLanguage === lang
                    ? "var(--primary)"
                    : "var(--glass-bg)",
                border: `1px solid ${
                  selectedLanguage === lang
                    ? "var(--primary-light)"
                    : "var(--glass-border)"
                }`,
                color:
                  selectedLanguage === lang
                    ? "#fff"
                    : "var(--text-secondary)",
              }}
            >
              {lang}
            </button>
          ))}
        </div>

        {/* Record / Text Toggle */}
        <div className="flex items-center justify-center gap-4">
          {!showTextMode ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={isListening ? stopRecording : startRecording}
              disabled={isProcessing}
              className="w-16 h-16 rounded-full flex items-center justify-center transition-all"
              style={{
                background: isListening
                  ? "var(--error)"
                  : "linear-gradient(135deg, var(--primary), var(--accent))",
                boxShadow: isListening
                  ? "0 0 30px rgba(239, 68, 68, 0.4)"
                  : "0 0 30px rgba(79, 70, 229, 0.3)",
                opacity: isProcessing ? 0.5 : 1,
                cursor: isProcessing ? "not-allowed" : "pointer",
              }}
            >
              {isListening ? (
                <svg width="24" height="24" fill="white" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : (
                <svg width="24" height="24" fill="white" viewBox="0 0 24 24">
                  <path d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="white" strokeWidth="2" fill="none" />
                  <line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2" />
                </svg>
              )}
            </motion.button>
          ) : (
            <form onSubmit={handleTextSubmit} className="flex-1 flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type your query in any language..."
                disabled={isProcessing}
                className="flex-1 px-4 py-3 rounded-xl text-sm outline-none transition-all"
                style={{
                  background: "var(--glass-bg)",
                  border: "1px solid var(--glass-border)",
                  color: "var(--text-primary)",
                }}
              />
              <button
                type="submit"
                disabled={isProcessing || !textInput.trim()}
                className="px-4 py-3 rounded-xl text-sm font-medium transition-all"
                style={{
                  background: "var(--primary)",
                  color: "#fff",
                  opacity: isProcessing || !textInput.trim() ? 0.5 : 1,
                }}
              >
                Send
              </button>
            </form>
          )}
        </div>

        {/* Mode toggle */}
        <div className="flex justify-center">
          <button
            onClick={() => setShowTextMode(!showTextMode)}
            className="text-xs transition-all hover:opacity-80"
            style={{ color: "var(--text-muted)" }}
          >
            {showTextMode ? "🎙️ Switch to Voice" : "⌨️ Switch to Text"}
          </button>
        </div>

        {/* Listening indicator */}
        {isListening && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="text-center text-sm"
            style={{ color: "var(--error)" }}
          >
            🔴 Recording... Tap to stop
          </motion.p>
        )}
      </footer>
    </main>
  );
}
