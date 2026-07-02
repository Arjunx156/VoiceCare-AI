/**
 * Shared date / currency formatters (en-IN locale) — replaces the inline
 * `new Date(...).toLocaleDateString(...)` copies across dashboard pages.
 */

export function formatDate(value: string | Date): string {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}

export function formatDateTime(value: string | Date): string {
  return new Date(value).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

const RELATIVE_UNITS: Array<[Intl.RelativeTimeFormatUnit, number]> = [
  ["year", 1000 * 60 * 60 * 24 * 365],
  ["month", 1000 * 60 * 60 * 24 * 30],
  ["day", 1000 * 60 * 60 * 24],
  ["hour", 1000 * 60 * 60],
  ["minute", 1000 * 60],
];

export function formatRelative(value: string | Date): string {
  const delta = new Date(value).getTime() - Date.now();
  const rtf = new Intl.RelativeTimeFormat("en-IN", { numeric: "auto" });
  for (const [unit, ms] of RELATIVE_UNITS) {
    if (Math.abs(delta) >= ms) {
      return rtf.format(Math.round(delta / ms), unit);
    }
  }
  return "just now";
}
