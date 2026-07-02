import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PriorityBadge, SentimentBadge, StatusBadge } from "./Badge";

describe("badges", () => {
  it("renders the status as visible text (never color-only)", () => {
    render(<StatusBadge status="Escalated" />);
    expect(screen.getByText("Escalated")).toBeInTheDocument();
  });

  it("renders priority and sentiment labels", () => {
    render(
      <>
        <PriorityBadge priority="Critical" />
        <SentimentBadge sentiment="Very Angry" />
      </>
    );
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("Very Angry")).toBeInTheDocument();
  });

  it("renders nothing for missing values", () => {
    const { container } = render(<StatusBadge status={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("still renders a readable label for unknown values", () => {
    render(<StatusBadge status="SomeNewStatus" />);
    expect(screen.getByText("SomeNewStatus")).toBeInTheDocument();
  });
});
