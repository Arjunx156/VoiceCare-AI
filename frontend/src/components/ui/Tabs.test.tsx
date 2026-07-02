import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { Tabs } from "./Tabs";

const TABS = [
  { value: "details", label: "Details" },
  { value: "replay", label: "Agent Replay" },
  { value: "handoff", label: "Handoff" },
];

function Harness() {
  const [tab, setTab] = useState("details");
  return (
    <Tabs tabs={TABS} value={tab} onChange={setTab}>
      <p>Active: {tab}</p>
    </Tabs>
  );
}

describe("Tabs", () => {
  it("exposes tablist/tab/tabpanel semantics", () => {
    render(<Harness />);
    expect(screen.getByRole("tablist")).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(3);
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Active: details");
    expect(screen.getByRole("tab", { name: "Details" })).toHaveAttribute("aria-selected", "true");
  });

  it("switches on click", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    await user.click(screen.getByRole("tab", { name: "Handoff" }));

    expect(screen.getByRole("tabpanel")).toHaveTextContent("Active: handoff");
    expect(screen.getByRole("tab", { name: "Handoff" })).toHaveAttribute("aria-selected", "true");
  });

  it("supports arrow-key navigation with wrap-around", async () => {
    const user = userEvent.setup();
    render(<Harness />);

    screen.getByRole("tab", { name: "Details" }).focus();
    await user.keyboard("{ArrowRight}");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Active: replay");

    await user.keyboard("{ArrowLeft}{ArrowLeft}");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Active: handoff");

    await user.keyboard("{Home}");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Active: details");

    await user.keyboard("{End}");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Active: handoff");
  });

  it("keeps only the active tab in the tab order (roving tabindex)", () => {
    render(<Harness />);
    expect(screen.getByRole("tab", { name: "Details" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Agent Replay" })).toHaveAttribute("tabindex", "-1");
  });
});
