import { clsx } from "clsx";
import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLDivElement> & {
  raised?: boolean;
  hover?: boolean;
  /** Layered surface + inset top highlight for depth (no glass). */
  elevated?: boolean;
};

/** House surface — 18px radius, 1px border, no shadow (see globals.css). */
export function Panel({ raised = false, hover = false, elevated = false, className, ...rest }: Props) {
  const base = elevated ? "panel-elevated" : raised ? "panel-raised" : "panel";
  return (
    <div className={clsx(base, hover && "panel-hover", className)} {...rest} />
  );
}
