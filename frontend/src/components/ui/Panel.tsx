import { clsx } from "clsx";
import type { HTMLAttributes } from "react";

type Props = HTMLAttributes<HTMLDivElement> & {
  raised?: boolean;
  hover?: boolean;
};

/** House surface — 18px radius, 1px border, no shadow (see globals.css). */
export function Panel({ raised = false, hover = false, className, ...rest }: Props) {
  return (
    <div
      className={clsx(raised ? "panel-raised" : "panel", hover && "panel-hover", className)}
      {...rest}
    />
  );
}
