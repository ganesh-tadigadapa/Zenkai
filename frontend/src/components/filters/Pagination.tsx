import Link from "next/link";

import { cx } from "@/lib/format";

export function Pagination({
  total,
  limit,
  offset,
  buildHref,
}: {
  total: number;
  limit: number;
  offset: number;
  buildHref: (offset: number) => string;
}) {
  if (total <= limit) return null;

  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  const hasPrevious = offset > 0;
  const hasNext = offset + limit < total;

  const base =
    "inline-flex h-9 items-center rounded-lg border px-3.5 text-[13px] font-medium transition-colors";

  return (
    <nav
      aria-label="Pagination"
      className="mt-8 flex items-center justify-between gap-3 border-t border-border pt-5"
    >
      <p className="tnum text-[12.5px] text-muted">
        Showing <span className="font-medium text-text">{offset + 1}</span>–
        <span className="font-medium text-text">{Math.min(offset + limit, total)}</span> of{" "}
        <span className="font-medium text-text">{total}</span>
      </p>

      <div className="flex items-center gap-2">
        {hasPrevious ? (
          <Link
            href={buildHref(Math.max(offset - limit, 0))}
            className={cx(base, "border-border-strong bg-surface text-text hover:bg-bg-subtle")}
            rel="prev"
          >
            Previous
          </Link>
        ) : (
          <span className={cx(base, "border-border bg-bg-subtle text-faint")} aria-disabled>
            Previous
          </span>
        )}

        <span className="tnum px-1 text-[12.5px] text-muted">
          {page} / {pages}
        </span>

        {hasNext ? (
          <Link
            href={buildHref(offset + limit)}
            className={cx(base, "border-border-strong bg-surface text-text hover:bg-bg-subtle")}
            rel="next"
          >
            Next
          </Link>
        ) : (
          <span className={cx(base, "border-border bg-bg-subtle text-faint")} aria-disabled>
            Next
          </span>
        )}
      </div>
    </nav>
  );
}
