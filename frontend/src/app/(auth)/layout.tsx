import Link from "next/link";

import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { BRAND } from "@/lib/brand";

/** A quiet, centred shell for sign-in and sign-up. No sidebar, no chrome. */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <header className="flex items-center justify-between px-5 py-5 sm:px-8">
        <Logo />
        <ThemeToggle />
      </header>

      <main id="main" className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-[400px]">{children}</div>
      </main>

      <footer className="px-5 py-6 text-center text-[12px] text-faint sm:px-8">
        <Link href="/" className="hover:text-text">
          {BRAND.tagline}
        </Link>
      </footer>
    </div>
  );
}
