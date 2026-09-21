import type { ReactNode } from "react";

import { ButtonLink } from "@/components/ui/Button";
import { IconAlert, IconInbox } from "@/components/ui/Icons";
import { cx } from "@/lib/format";

export function EmptyState({
  title,
  body,
  action,
  icon,
  className,
}: {
  title: string;
  body?: string;
  action?: { href: string; label: string };
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cx(
        "flex flex-col items-center justify-center rounded-panel border border-dashed border-border",
        "bg-bg-subtle/50 px-6 py-14 text-center",
        className,
      )}
    >
      <span className="mb-3 grid size-11 place-items-center rounded-full bg-surface text-[18px] text-faint shadow-card">
        {icon ?? <IconInbox />}
      </span>
      <h3 className="text-sm font-semibold text-text">{title}</h3>
      {body ? <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-muted">{body}</p> : null}
      {action ? (
        <ButtonLink href={action.href} variant="secondary" size="sm" className="mt-4">
          {action.label}
        </ButtonLink>
      ) : null}
    </div>
  );
}

/**
 * Shown whenever an API call fails. It names the likely cause rather than
 * saying "something went wrong", because the most common cause in development
 * is simply that the backend is not running.
 */
export function ErrorState({
  title = "Could not load opportunities",
  message,
  hint = "Check that the Zenkai API is running on the configured NEXT_PUBLIC_API_URL.",
}: {
  title?: string;
  message?: string;
  hint?: string;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center rounded-panel border border-expired/30 bg-expired-soft px-6 py-12 text-center"
    >
      <span className="mb-3 grid size-11 place-items-center rounded-full bg-surface text-[18px] text-expired shadow-card">
        <IconAlert />
      </span>
      <h3 className="text-sm font-semibold text-text">{title}</h3>
      {message ? <p className="mt-1.5 text-[13px] text-expired">{message}</p> : null}
      <p className="mt-2 max-w-md text-[12px] leading-relaxed text-muted">{hint}</p>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-panel border border-border bg-surface p-5">
      <div className="skeleton h-3 w-24 rounded" />
      <div className="skeleton mt-2.5 h-4 w-3/4 rounded" />
      <div className="skeleton mt-3 h-3 w-full rounded" />
      <div className="skeleton mt-1.5 h-3 w-5/6 rounded" />
      <div className="mt-4 flex gap-1.5">
        <div className="skeleton h-5 w-20 rounded-md" />
        <div className="skeleton h-5 w-14 rounded-md" />
        <div className="skeleton h-5 w-16 rounded-md" />
      </div>
      <div className="skeleton mt-5 h-3 w-1/3 rounded" />
    </div>
  );
}

export function GridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-busy="true" aria-live="polite">
      {Array.from({ length: count }, (_, index) => (
        <CardSkeleton key={index} />
      ))}
      <span className="sr-only">Loading opportunities…</span>
    </div>
  );
}

export function RowSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-2" aria-busy="true">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="skeleton h-[58px] rounded-card" />
      ))}
    </div>
  );
}
