"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Progressively reveals `text` word-by-word for a "typing" feel, used on the
 * latest assistant turn so the answer appears to be spoken/typed in real time.
 * When `enabled` is false the full text is shown immediately (past turns).
 */
export function useTypewriter(text: string, enabled: boolean, wordsPerTick = 2, tickMs = 45): string {
  const [shown, setShown] = useState(enabled ? "" : text);
  const startedFor = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setShown(text);
      return;
    }
    // Restart the reveal whenever the target text changes (a new turn).
    if (startedFor.current === text) return;
    startedFor.current = text;

    const words = text.split(/(\s+)/); // keep whitespace tokens to preserve spacing
    let i = 0;
    setShown("");
    const id = setInterval(() => {
      i += wordsPerTick * 2; // account for interleaved whitespace tokens
      setShown(words.slice(0, i).join(""));
      if (i >= words.length) {
        setShown(text);
        clearInterval(id);
      }
    }, tickMs);

    return () => clearInterval(id);
  }, [text, enabled, wordsPerTick, tickMs]);

  return shown;
}
