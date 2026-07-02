"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

import { useMotionSafe } from "@/lib/motion";

type Props = {
  eyebrow: string;
  title: ReactNode;
  subtitle?: ReactNode;
  /** Right-aligned actions (filters, buttons). */
  actions?: ReactNode;
};

/** Standard page header: coral eyebrow over a bold title, actions on the right. */
export function PageHeader({ eyebrow, title, subtitle, actions }: Props) {
  const { entry } = useMotionSafe();

  return (
    <motion.header
      {...entry()}
      style={{
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 16,
      }}
    >
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{subtitle}</p>
        )}
      </div>
      {actions && <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>{actions}</div>}
    </motion.header>
  );
}
