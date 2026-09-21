import Link from "next/link";

import { BRAND } from "@/lib/brand";
import { cx } from "@/lib/format";

/**
 * The Zenkai mark: a radar sweep. Concentric rings with a single sweep arm and
 * one detected blip — the product's idea in one glyph.
 */
export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cx(
        "grid size-7 shrink-0 place-items-center rounded-[8px] bg-text text-bg",
        className,
      )}
    >
      <svg viewBox="0 0 24 24" className="size-[15px]" aria-hidden="true">
        <circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" strokeWidth="1.6" opacity="0.45" />
        <circle cx="12" cy="12" r="4.75" fill="none" stroke="currentColor" strokeWidth="1.6" opacity="0.75" />
        <path
          d="M12 12 L12 3.5"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
        <circle cx="12" cy="12" r="1.7" fill="currentColor" />
        <circle cx="17.4" cy="7.2" r="1.5" fill="currentColor" />
      </svg>
    </span>
  );
}

export function Logo({
  href = "/",
  className,
  showTagline = false,
}: {
  href?: string;
  className?: string;
  showTagline?: boolean;
}) {
  return (
    <Link
      href={href}
      aria-label={`${BRAND.name} — ${BRAND.tagline}`}
      className={cx("inline-flex items-center gap-2.5", className)}
    >
      <LogoMark />
      <span className="flex flex-col leading-none">
        <span className="text-[15px] font-semibold tracking-[0.14em] text-text">
          ZEN<span className="text-accent">KAI</span>
        </span>
        {showTagline ? (
          <span className="mt-1 text-[10.5px] font-medium tracking-[0.02em] text-faint">
            {BRAND.tagline}
          </span>
        ) : null}
      </span>
    </Link>
  );
}
