import type { ReactNode } from "react";

import { IconExternal } from "@/components/ui/Icons";

/**
 * Every link that leaves Zenkai goes through here.
 *
 * Centralised so the safety attributes cannot be forgotten on one link and
 * present on another: `noopener` denies the opened page access to
 * `window.opener`, `noreferrer` withholds the referrer, and `nofollow` avoids
 * passing ranking signal to pages we merely catalogue.
 *
 * A missing or unusable URL renders nothing rather than a dead control.
 */
export function ExternalLink({
  href,
  children,
  className,
  showIcon = true,
  title,
  ariaLabel,
}: {
  href: string | null | undefined;
  children: ReactNode;
  className?: string;
  showIcon?: boolean;
  title?: string;
  ariaLabel?: string;
}) {
  if (!isSafeExternalUrl(href)) return null;

  return (
    <a
      href={href as string}
      target="_blank"
      rel="noopener noreferrer nofollow"
      title={title}
      aria-label={ariaLabel}
      className={className}
    >
      {children}
      {showIcon ? <IconExternal className="text-[0.85em]" aria-hidden /> : null}
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

/** Only http(s) is followed — never javascript:, data: or a relative path. */
export function isSafeExternalUrl(href: string | null | undefined): boolean {
  if (!href) return false;
  try {
    const { protocol } = new URL(href);
    return protocol === "https:" || protocol === "http:";
  } catch {
    return false;
  }
}

/** "education.github.com" — the recognisable part of a URL, for display. */
export function hostOf(href: string | null | undefined): string {
  if (!href) return "";
  try {
    return new URL(href).hostname.replace(/^www\./, "");
  } catch {
    return href;
  }
}
