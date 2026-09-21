"use client";

import { IconMoon, IconSun } from "@/components/ui/Icons";
import { STORAGE_KEYS } from "@/lib/brand";

/**
 * Theme control with no React state.
 *
 * Which glyph shows is decided in CSS from the same `data-theme` / media-query
 * rules that colour the page (see globals.css). That removes the mount flash a
 * state-based toggle needs, and keeps server and client markup identical.
 */
export function ThemeToggle() {
  function toggle() {
    const root = document.documentElement;
    const explicit = root.dataset.theme;
    const current =
      explicit ??
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";

    root.dataset.theme = next;
    try {
      localStorage.setItem(STORAGE_KEYS.theme, next);
    } catch {
      /* private browsing — the choice simply won't persist */
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle between light and dark theme"
      title="Toggle theme"
      className="grid size-9 place-items-center rounded-lg border border-border bg-surface text-[15px] text-muted transition-colors hover:bg-bg-subtle hover:text-text"
    >
      <IconMoon className="theme-light-only" />
      <IconSun className="theme-dark-only" />
    </button>
  );
}
