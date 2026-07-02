"use client";

import { useId, useRef } from "react";
import type { ReactNode } from "react";

export type TabItem = {
  value: string;
  label: ReactNode;
};

type Props = {
  tabs: TabItem[];
  value: string;
  onChange: (value: string) => void;
  /** Content of the active tab (rendered inside the tabpanel). */
  children: ReactNode;
};

/**
 * Accessible tabs: real tablist/tab/tabpanel roles, roving tabindex, and
 * Left/Right/Home/End keyboard navigation. Styling follows the pill system.
 */
export function Tabs({ tabs, value, onChange, children }: Props) {
  const baseId = useId();
  const listRef = useRef<HTMLDivElement>(null);

  const activeIndex = Math.max(0, tabs.findIndex((tab) => tab.value === value));

  const focusTab = (index: number) => {
    const clamped = (index + tabs.length) % tabs.length;
    onChange(tabs[clamped].value);
    const buttons = listRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
    buttons?.[clamped]?.focus();
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "ArrowRight":
        event.preventDefault();
        focusTab(activeIndex + 1);
        break;
      case "ArrowLeft":
        event.preventDefault();
        focusTab(activeIndex - 1);
        break;
      case "Home":
        event.preventDefault();
        focusTab(0);
        break;
      case "End":
        event.preventDefault();
        focusTab(tabs.length - 1);
        break;
    }
  };

  return (
    <div>
      <div
        ref={listRef}
        role="tablist"
        onKeyDown={handleKeyDown}
        style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
      >
        {tabs.map((tab, index) => {
          const isActive = index === activeIndex;
          return (
            <button
              key={tab.value}
              type="button"
              role="tab"
              id={`${baseId}-tab-${tab.value}`}
              aria-selected={isActive}
              aria-controls={`${baseId}-panel-${tab.value}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => onChange(tab.value)}
              className="lang-pill"
              style={
                isActive
                  ? {
                      color: "var(--accent)",
                      borderColor: "var(--accent-border)",
                      background: "var(--accent-dim)",
                      fontSize: 12,
                      fontWeight: 600,
                    }
                  : { fontSize: 12 }
              }
            >
              {tab.label}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={`${baseId}-panel-${tabs[activeIndex]?.value}`}
        aria-labelledby={`${baseId}-tab-${tabs[activeIndex]?.value}`}
        style={{ marginTop: 20 }}
      >
        {children}
      </div>
    </div>
  );
}
