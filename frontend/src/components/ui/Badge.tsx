import type { ReactNode } from "react";

import { cx } from "@/lib/format";

type Tone = "neutral" | "accent" | "verified" | "review" | "expired" | "critical" | "soon" | "calm";

const TONES: Record<Tone, string> = {
  neutral: "bg-bg-subtle text-muted border-border",
  accent: "bg-accent-soft text-accent border-transparent",
  verified: "bg-verified-soft text-verified border-transparent",
  review: "bg-review-soft text-review border-transparent",
  expired: "bg-expired-soft text-expired border-transparent",
  critical: "bg-critical-soft text-critical border-transparent",
  soon: "bg-soon-soft text-soon border-transparent",
  calm: "bg-calm-soft text-calm border-transparent",
};

export function Badge({
  children,
  tone = "neutral",
  className,
  title,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
  title?: string;
}) {
  return (
    <span
      title={title}
      className={cx(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-2 py-0.5",
        "text-[11px] font-medium leading-5 tracking-[0.01em]",
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Dot({ className }: { className?: string }) {
  return <span aria-hidden className={cx("size-1.5 shrink-0 rounded-full", className)} />;
}
