import { useState, useRef, useCallback, useEffect } from "react";
import { createWebSocket, clearConversation, type VoiceQueryResponse } from "@/lib/api";
import { LANG_TO_BCP47 } from "@/lib/constants";
import { parseWsMessage } from "@/lib/ws-messages";

// Stable error codes — translated in the view layer via t("error.<code>")
export type VoiceErrorCode = "micDenied" | "connection" | "connectionLost" | "generic";

// One completed exchange in the visible conversation thread.
export interface ConversationTurn {
  customer: string;          // what the customer said/typed ("" for voice with no transcript)
  ai: VoiceQueryResponse;    // the assistant's full response for this turn
}

// Minimal type shim for the browser Web Speech API (not in TS lib by default)
interface SpeechRecognitionInstance {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: { length: number; [i: number]: { isFinal: boolean; [j: number]: { transcript: string } } };
}

const MAX_WS_RETRIES = 3;
const LS_LANG_KEY = "vc_lang";
const DEFAULT_LANG = "Hindi";

function readStoredLang(): string {
  if (typeof window === "undefined") return DEFAULT_LANG;
  return localStorage.getItem(LS_LANG_KEY) ?? DEFAULT_LANG;
}

export function useVoiceInteraction() {
  const [isListening, setIsListening]     = useState(false);
  const [isProcessing, setIsProcessing]   = useState(false);
  const [currentStage, setCurrentStage]   = useState(0);
  const [isComplete, setIsComplete]       = useState(false);
  const [response, setResponse]           = useState<VoiceQueryResponse | null>(null);
  // Full visible history of completed turns this conversation (persists across
  // mic presses; cleared only on "New conversation").
  const [turns, setTurns]                 = useState<ConversationTurn[]>([]);
  // error holds a translated string (set by the view) or a raw error code string
  // after the refactor it will hold a VoiceErrorCode; VoiceView maps it via t()
  const [errorCode, setErrorCode]         = useState<VoiceErrorCode | null>(null);
  const [selectedLanguage, setSelectedLanguageState] = useState<string>(DEFAULT_LANG);
  // Session is in-memory only: each fresh page mount starts a new conversation,
  // so a new complaint after navigating away never merges with an old one.
  // Follow-ups within a single visit still continue (the hook isn't remounted
  // between mic presses).
  const [sessionId, setSessionId]         = useState<string | null>(null);
  const [phone, setPhone]                 = useState<string>("");
  const [textInput, setTextInput]         = useState("");
  const [showTextMode, setShowTextMode]   = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [bhashiniWarning, setBhashiniWarning] = useState(false);

  // Load persisted language on first client render. This must happen after
  // hydration (server HTML renders the default), so the sync setState here
  // is the intended SSR-safe localStorage pattern.
  useEffect(() => {
    const stored = readStoredLang();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- post-hydration localStorage read; server cannot know the stored language
    if (stored !== DEFAULT_LANG) setSelectedLanguageState(stored);
  }, []);

  // Persist language whenever it changes
  const setSelectedLanguage = useCallback((lang: string) => {
    setSelectedLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem(LS_LANG_KEY, lang);
    }
  }, []);

  // Live mic amplitude (0-1), written every animation frame. A ref — NOT
  // state — so metering never re-renders the React tree at 60fps; the orb
  // reads it inside its own useFrame loop.
  const audioLevelRef     = useRef(0);
  const mediaRecorderRef  = useRef<MediaRecorder | null>(null);
  const audioChunksRef    = useRef<Blob[]>([]);
  const analyserRef       = useRef<AnalyserNode | null>(null);
  const animFrameRef      = useRef<number>(0);
  const streamRef         = useRef<MediaStream | null>(null);
  const recognitionRef    = useRef<SpeechRecognitionInstance | null>(null);
  const transcriptAccRef  = useRef<string>("");
  // Hold a strong reference to the playing Audio element so the GC cannot
  // collect it before playback finishes (local-variable Audio objects get
  // collected mid-play in some browser/engine combinations).
  const audioRef          = useRef<HTMLAudioElement | null>(null);
  // Timer id for the Chrome SpeechSynthesis resume-workaround (see below).
  const ttsTimerRef       = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopCurrentTTS = useCallback(() => {
    if (ttsTimerRef.current) {
      clearInterval(ttsTimerRef.current);
      ttsTimerRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }, []);

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (recognitionRef.current) recognitionRef.current.stop();
      stopCurrentTTS();
    };
  }, [stopCurrentTTS]);

  const playBrowserTTS = useCallback((text: string, lang?: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    // Cancel any in-progress speech before starting a new one.
    window.speechSynthesis.cancel();
    if (ttsTimerRef.current) clearInterval(ttsTimerRef.current);

    const bcp47 = (lang ? LANG_TO_BCP47[lang] : undefined) ?? "en-US";
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = bcp47;

    // Chrome silently stops long utterances (~14 s). Pause/resume every 10 s
    // resets the internal timer, allowing arbitrarily long speech to complete.
    ttsTimerRef.current = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      } else {
        clearInterval(ttsTimerRef.current!);
        ttsTimerRef.current = null;
      }
    }, 10_000);

    utterance.onend = () => {
      if (ttsTimerRef.current) clearInterval(ttsTimerRef.current);
      ttsTimerRef.current = null;
    };
    utterance.onerror = () => {
      if (ttsTimerRef.current) clearInterval(ttsTimerRef.current);
      ttsTimerRef.current = null;
    };

    window.speechSynthesis.speak(utterance);
  }, []);

  /**
   * Detect MIME type from the base64 payload.
   * The backend prefixes Google-TTS fallback audio with "mp3:" so we can
   * distinguish it from Bhashini WAV audio without inspecting magic bytes.
   * If no prefix is present, inspect the first decoded bytes.
   */
  const resolveAudio = useCallback((raw: string): { mime: string; b64: string } => {
    if (raw.startsWith("mp3:")) {
      return { mime: "audio/mpeg", b64: raw.slice(4) };
    }
    // Inspect first 4 bytes to distinguish WAV ("RIFF") from MP3 (0xFF 0xFx / "ID3")
    try {
      const header = atob(raw.slice(0, 8));
      if (header.startsWith("RIFF")) return { mime: "audio/wav", b64: raw };
      const b0 = header.charCodeAt(0), b1 = header.charCodeAt(1);
      if (header.startsWith("ID3") || (b0 === 0xff && (b1 & 0xe0) === 0xe0)) {
        return { mime: "audio/mpeg", b64: raw };
      }
    } catch { /* ignore decode errors, fall through */ }
    return { mime: "audio/wav", b64: raw }; // Bhashini default
  }, []);

  const playAudioResponse = useCallback((base64Audio?: string, text?: string, lang?: string) => {
    // Stop anything already playing before starting a new response.
    stopCurrentTTS();

    if (base64Audio) {
      const { mime, b64 } = resolveAudio(base64Audio);
      // Store in a ref so the GC cannot collect the element before it finishes.
      const audio = new Audio(`data:${mime};base64,${b64}`);
      audioRef.current = audio;
      audio.onended = () => { audioRef.current = null; };
      audio.play().catch((e) => {
        console.error("Audio playback failed, falling back to browser TTS", e);
        audioRef.current = null;
        if (text) playBrowserTTS(text, lang);
      });
    } else if (text) {
      playBrowserTTS(text, lang);
    }
  }, [playBrowserTTS, stopCurrentTTS, resolveAudio]);

  const processQuery = useCallback(
    (overrides: { text?: string; audio_base64?: string } = {}, initialRetryCount = 0) => {
      const currentSessionId = sessionId || crypto.randomUUID();
      if (!sessionId) {
        setSessionId(currentSessionId);
      }

      // Hoisted so the reconnect path can self-reference without touching the
      // outer useCallback binding before its declaration completes.
      function attempt(retryCount: number) {
      setIsProcessing(true);
      setCurrentStage(1);

      let completed = false;

      try {
        const ws = createWebSocket(currentSessionId);

        ws.onopen = () => {
          ws.send(JSON.stringify({
            text: overrides.text,
            audio_base64: overrides.audio_base64,
            language: selectedLanguage,
            phone: phone || undefined,
          }));
        };

        ws.onmessage = (event) => {
          const message = parseWsMessage(event.data);

          switch (message.kind) {
            case "ping":
            case "unknown":
              return; // keep-alive / unrecognized frames are ignored

            case "stage":
              setCurrentStage(message.stageNumber);
              return;

            case "response": {
              completed = true;
              const ai = message.response;
              setCurrentStage(9);
              setResponse(ai);
              setTurns((prev) => [...prev, { customer: overrides.text ?? "", ai }]);
              setIsComplete(true);
              playAudioResponse(ai.response_audio_base64, ai.response_text, selectedLanguage);
              setIsProcessing(false);
              ws.close();
              return;
            }

            case "error":
              completed = true;
              setErrorCode("generic");
              setIsProcessing(false);
              ws.close();
              return;
          }
        };

        ws.onerror = (err) => {
          console.error("WebSocket error:", err);
          completed = true;
          setErrorCode("connection");
          setIsProcessing(false);
          ws.close();
        };

        ws.onclose = (event) => {
          if (!event.wasClean && !completed) {
            if (retryCount < MAX_WS_RETRIES) {
              const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
              console.warn(`WebSocket closed unexpectedly, retrying in ${delay}ms (attempt ${retryCount + 1}/${MAX_WS_RETRIES})`);
              setTimeout(() => attempt(retryCount + 1), delay);
            } else {
              setErrorCode("connectionLost");
              setIsProcessing(false);
            }
          }
        };
      } catch (err: unknown) {
        console.error("WebSocket setup error:", err);
        setErrorCode("generic");
        setIsProcessing(false);
      }
      }

      attempt(initialRetryCount);
    },
    [selectedLanguage, sessionId, phone, playAudioResponse]
  );

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
      audioLevelRef.current = avg / 255;
      animFrameRef.current = requestAnimationFrame(update);
    };
    update();
  }, []);

  const startSpeechRecognition = useCallback((language: string) => {
    const w = window as Window & { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance };
    const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!SR) return;
    transcriptAccRef.current = "";
    setLiveTranscript("");
    const recognition = new SR();
    recognition.lang = LANG_TO_BCP47[language] || "hi-IN";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event: SpeechRecognitionEvent) => {
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
      // Stop any audio that's still playing from the previous response.
      stopCurrentTTS();
      setErrorCode(null);
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
        if (recognitionRef.current) {
          recognitionRef.current.stop();
          recognitionRef.current = null;
        }
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        stream.getTracks().forEach((t) => t.stop());
        audioLevelRef.current = 0;
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
      setErrorCode("micDenied");
    }
  }, [monitorAudio, startSpeechRecognition, selectedLanguage, processQuery, stopCurrentTTS]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const handleTextSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || isProcessing) return;
    processQuery({ text: textInput.trim() });
    setTextInput("");
  }, [textInput, isProcessing, processQuery]);

  const startNewConversation = useCallback(async () => {
    stopCurrentTTS();
    // Clear server-side memory for the current session
    if (sessionId) {
      try { await clearConversation(sessionId); } catch { /* best-effort */ }
    }
    // Generate a fresh session and reset all UI state
    const newId = crypto.randomUUID();
    setSessionId(newId);
    setResponse(null);
    setTurns([]);
    setIsComplete(false);
    setCurrentStage(0);
    setErrorCode(null);
    setLiveTranscript("");
    setTextInput("");
    setPhone("");
  }, [sessionId, stopCurrentTTS]);

  return {
    isListening,
    isProcessing,
    isComplete,
    audioLevelRef,
    currentStage,
    response,
    turns,
    errorCode,
    selectedLanguage,
    setSelectedLanguage,
    phone,
    setPhone,
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
    sessionId,
  };
}
