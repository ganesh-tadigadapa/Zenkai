import Link from "next/link";

import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

/** The floating header on the landing page: logo, browse, sign in, theme. */
export function LandingHeader() {
  return (
    <header className="fixed inset-x-0 top-3 z-40 px-3 sm:top-4">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-4 rounded-full border border-border/80 bg-surface/60 pl-4 pr-2 shadow-[var(--shadow-md)] backdrop-blur-xl sm:pl-5">
        <Logo />
        <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/opportunities"
            className="hidden px-3 py-2 text-[13px] text-muted transition-colors hover:text-text sm:block"
          >
            Browse
          </Link>
          <Link
            href="/login"
            className="px-3 py-2 text-[13px] text-muted transition-colors hover:text-text"
          >
            Sign in
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
