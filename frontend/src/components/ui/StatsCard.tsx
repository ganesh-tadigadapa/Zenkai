import Link from "next/link";
import type { ReactNode } from "react";

import { cx } from "@/lib/format";

export function StatsCard({
  label,
  value,
  hint,
  href,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: number | string;
  hint?: string;
  href?: string;
  tone?: "neutral" | "accent" | "critical" | "verified";
  icon?: ReactNode;
}) {
  const accentBar = {
    neutral: "bg-border-strong",
    accent: "bg-accent",
    critical: "bg-critical",
    verified: "bg-verified",
  }[tone];

  const content = (
    <>
      <span className={cx("absolute inset-x-0 top-0 h-[2px] rounded-t-panel", accentBar)} />
      <div className="flex items-start justify-between gap-2">
        <p className="text-[12px] font-medium text-muted">{label}</p>
        {icon ? <span className="text-[14px] text-faint">{icon}</span> : null}
      </div>
      <p className="tnum mt-2 text-[26px] font-semibold leading-none tracking-[-0.02em] text-text">
        {value}
      </p>
      {hint ? <p className="mt-1.5 text-[11.5px] text-faint">{hint}</p> : null}
    </>
  );

  const className = cx(
    "relative overflow-hidden rounded-panel border border-border bg-surface p-4",
    href && "transition-colors hover:border-border-strong hover:bg-bg-subtle",
  );

  return href ? (
    <Link href={href} className={className}>
      {content}
    </Link>
  ) : (
    <div className={className}>{content}</div>
  );
}
