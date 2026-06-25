import { useState, useRef, useCallback, useEffect } from "react";
import { sendVoiceQuery, type VoiceQueryResponse } from "@/lib/api";

const LANG_TO_BCP47: Record<string, string> = {
  Hindi: "hi-IN", English: "en-IN", Malayalam: "ml-IN", Tamil: "ta-IN",
  Telugu: "te-IN", Kannada: "kn-IN", Bengali: "bn-IN", Marathi: "mr-IN",
  Hinglish: "hi-IN",
};

export function useVoiceInteraction() {
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
  const recognitionRef    = useRef<unknown>(null);
  const transcriptAccRef  = useRef<string>("");

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if (recognitionRef.current) (recognitionRef.current as any).stop();
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
        setSessionId(result.session_id || null);
        setIsComplete(true);
        playAudioResponse(result.response_audio_base64, result.response_text, selectedLanguage);
      } catch (err: unknown) {
        clearInterval(stageInterval);
        const msg: string = err instanceof Error ? err.message : "Something went wrong. Please try again.";
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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    transcriptAccRef.current = "";
    setLiveTranscript("");
    const recognition = new SR();
    recognition.lang = LANG_TO_BCP47[language] || "hi-IN";
    recognition.continuous = true;
    recognition.interimResults = true;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (recognition as any).start();
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
        if (recognitionRef.current) { 
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (recognitionRef.current as any).stop(); 
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
      setError("Microphone access denied. Please allow microphone access.");
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
    error,
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
