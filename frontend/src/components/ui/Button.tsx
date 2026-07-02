"use client";

import { clsx } from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Spinner } from "./Spinner";

type ButtonVariant = "primary" | "ghost" | "danger";
type ButtonSize = "md" | "sm";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  children: ReactNode;
};

const VARIANT_STYLE: Record<ButtonVariant, React.CSSProperties> = {
  primary: { background: "var(--accent)", color: "#fff" },
  ghost: {
    background: "transparent",
    color: "var(--text-secondary)",
    border: "1px solid var(--border-subtle)",
  },
  danger: {
    background: "rgba(229,57,53,0.12)",
    color: "var(--status-high)",
    border: "1px solid rgba(229,57,53,0.3)",
  },
};

const SIZE_STYLE: Record<ButtonSize, React.CSSProperties> = {
  md: { padding: "10px 24px", fontSize: 14 },
  sm: { padding: "6px 16px", fontSize: 12 },
};

/** House pill button. Hover/active/disabled states come from .btn-pill. */
export function Button({
  variant = "primary",
  size = "md",
  isLoading = false,
  disabled,
  children,
  style,
  className,
  type = "button",
  ...rest
}: Props) {
  return (
    <button
      type={type}
      className={clsx("btn-pill", className)}
      disabled={disabled || isLoading}
      style={{ ...VARIANT_STYLE[variant], ...SIZE_STYLE[size], ...style }}
      {...rest}
    >
      {isLoading && <Spinner size={14} />}
      {children}
    </button>
  );
}
