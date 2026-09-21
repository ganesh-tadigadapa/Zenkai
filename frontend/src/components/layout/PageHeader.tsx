import type { ReactNode } from "react";

import { cx } from "@/lib/format";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx("flex flex-wrap items-end justify-between gap-4 pb-6", className)}>
      <div className="min-w-0">
        {eyebrow ? (
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-faint">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="text-balance text-[22px] font-semibold leading-tight tracking-[-0.015em] text-text sm:text-[26px]">
          {title}
        </h1>
        {description ? (
          <p className="mt-1.5 max-w-2xl text-[13.5px] leading-relaxed text-muted">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function SectionHeader({
  title,
  description,
  action,
}: {
  title: ReactNode;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
      <div>
        <h2 className="text-[15px] font-semibold tracking-[-0.01em] text-text">{title}</h2>
        {description ? <p className="mt-0.5 text-[12.5px] text-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
