import { useState, useRef, useCallback, useEffect } from "react";
import { createWebSocket, type VoiceQueryResponse } from "@/lib/api";
import { LANG_TO_BCP47 } from "@/lib/constants";

// Stable error codes — translated in the view layer via t("error.<code>")
export type VoiceErrorCode = "micDenied" | "connection" | "connectionLost" | "generic";

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
  const [audioLevel, setAudioLevel]       = useState(0);
  const [currentStage, setCurrentStage]   = useState(0);
  const [isComplete, setIsComplete]       = useState(false);
  const [response, setResponse]           = useState<VoiceQueryResponse | null>(null);
  // error holds a translated string (set by the view) or a raw error code string
  // after the refactor it will hold a VoiceErrorCode; VoiceView maps it via t()
  const [errorCode, setErrorCode]         = useState<VoiceErrorCode | null>(null);
  const [selectedLanguage, setSelectedLanguageState] = useState<string>(DEFAULT_LANG);
  const [sessionId, setSessionId]         = useState<string | null>(null);
  const [textInput, setTextInput]         = useState("");
  const [showTextMode, setShowTextMode]   = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [bhashiniWarning, setBhashiniWarning] = useState(false);

  // Load persisted language on first client render
  useEffect(() => {
    setSelectedLanguageState(readStoredLang());
  }, []);

  // Persist language whenever it changes
  const setSelectedLanguage = useCallback((lang: string) => {
    setSelectedLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem(LS_LANG_KEY, lang);
    }
  }, []);

  const mediaRecorderRef  = useRef<MediaRecorder | null>(null);
  const audioChunksRef    = useRef<Blob[]>([]);
  const analyserRef       = useRef<AnalyserNode | null>(null);
  const animFrameRef      = useRef<number>(0);
  const streamRef         = useRef<MediaStream | null>(null);
  const recognitionRef    = useRef<SpeechRecognitionInstance | null>(null);
  const transcriptAccRef  = useRef<string>("");

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  const playBrowserTTS = useCallback((text: string, lang?: string) => {
    if (window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = LANG_TO_BCP47[lang || "en-US"] || "en-US";
      window.speechSynthesis.speak(utterance);
    }
  }, []);

  const playAudioResponse = useCallback((base64Audio?: string, text?: string, lang?: string) => {
    if (base64Audio) {
      const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);
      audio.play().catch((e) => {
        console.error("Audio playback failed", e);
        if (text) playBrowserTTS(text, lang);
      });
    } else if (text) {
      playBrowserTTS(text, lang);
    }
  }, [playBrowserTTS]);

  const processQuery = useCallback(
    (overrides: { text?: string; audio_base64?: string } = {}, retryCount = 0) => {
      setIsProcessing(true);
      setCurrentStage(1);

      const currentSessionId = sessionId || crypto.randomUUID();
      if (!sessionId) setSessionId(currentSessionId);

      let completed = false;

      try {
        const ws = createWebSocket(currentSessionId);

        ws.onopen = () => {
          ws.send(JSON.stringify({
            text: overrides.text,
            audio_base64: overrides.audio_base64,
            language: selectedLanguage,
          }));
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.type === "response") {
            completed = true;
            setCurrentStage(9);
            setResponse(data as VoiceQueryResponse);
            setIsComplete(true);
            playAudioResponse(data.response_audio_base64, data.response_text, selectedLanguage);
            setIsProcessing(false);
            ws.close();
          } else if (data.stage_number) {
            setCurrentStage(data.stage_number);
          } else if (data.error) {
            completed = true;
            setErrorCode("generic");
            setIsProcessing(false);
            ws.close();
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
              setTimeout(() => processQuery(overrides, retryCount + 1), delay);
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
    },
    [selectedLanguage, sessionId, playAudioResponse]
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
      setAudioLevel(avg / 255);
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
      setErrorCode("micDenied");
    }
  }, [monitorAudio, startSpeechRecognition, selectedLanguage, processQuery]);

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

  return {
    isListening,
    isProcessing,
    isComplete,
    audioLevel,
    currentStage,
    response,
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
  };
}
