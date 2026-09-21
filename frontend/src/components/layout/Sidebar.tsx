"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import {
  IconAward,
  IconBookmark,
  IconBriefcase,
  IconClock,
  IconGraduationCap,
  IconGrid,
  IconMenu,
  IconRadar,
  IconShield,
  IconSparkles,
  IconTrophy,
  IconUser,
  IconUsers,
  IconX,
} from "@/components/ui/Icons";
import { cx } from "@/lib/format";

interface NavItem {
  href: string;
  label: string;
  icon: typeof IconGrid;
  badge?: number;
}

const PRIMARY: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: IconGrid },
  { href: "/opportunities", label: "Opportunities", icon: IconRadar },
];

const CATEGORIES: NavItem[] = [
  { href: "/opportunities?category=certifications", label: "Certifications", icon: IconAward },
  { href: "/opportunities?category=internships", label: "Internships", icon: IconBriefcase },
  { href: "/opportunities?category=hackathons", label: "Hackathons", icon: IconTrophy },
  { href: "/opportunities?category=programs", label: "Programs", icon: IconUsers },
  { href: "/opportunities?category=tech_benefits", label: "Tech Benefits", icon: IconSparkles },
  { href: "/opportunities?category=scholarships", label: "Scholarships", icon: IconGraduationCap },
];

const PERSONAL: NavItem[] = [
  { href: "/saved", label: "Saved", icon: IconBookmark },
  { href: "/deadlines", label: "Deadlines", icon: IconClock },
  { href: "/profile", label: "Profile", icon: IconUser },
];

const ADMIN: NavItem[] = [{ href: "/admin", label: "Review queue", icon: IconShield }];

function NavLink({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const pathname = usePathname();
  const [path, query] = item.href.split("?");
  // A category link is active only when the pathname matches and, for the plain
  // feed link, no category filter is applied.
  const active =
    pathname === path && (query ? false : true);

  const Glyph = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cx(
        "flex items-center gap-2.5 rounded-lg px-2.5 py-[7px] text-[13px] font-medium transition-colors",
        active
          ? "bg-accent-soft text-accent"
          : "text-muted hover:bg-bg-subtle hover:text-text",
      )}
    >
      <Glyph className="text-[15px]" />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

function Section({
  title,
  items,
  onNavigate,
}: {
  title?: string;
  items: NavItem[];
  onNavigate?: () => void;
}) {
  return (
    <div className="space-y-0.5">
      {title ? (
        <p className="px-2.5 pb-1.5 pt-4 text-[10px] font-semibold uppercase tracking-[0.08em] text-faint">
          {title}
        </p>
      ) : null}
      {items.map((item) => (
        <NavLink key={item.href} item={item} onNavigate={onNavigate} />
      ))}
    </div>
  );
}

function NavContent({
  onNavigate,
  user,
}: {
  onNavigate?: () => void;
  user?: { is_admin: boolean } | null;
}) {
  return (
    <nav aria-label="Main" className="flex flex-col gap-0.5 px-3 pb-6">
      <Section items={PRIMARY} onNavigate={onNavigate} />
      <Section title="Categories" items={CATEGORIES} onNavigate={onNavigate} />
      {/* Personal surfaces are pointless without an account, so they are not
          offered to a signed-out visitor browsing the catalogue. */}
      {user ? <Section title="Yours" items={PERSONAL} onNavigate={onNavigate} /> : null}
      {/* The review queue is a reviewer tool; it is not advertised to students. */}
      {user?.is_admin ? (
        <Section title="Operations" items={ADMIN} onNavigate={onNavigate} />
      ) : null}
    </nav>
  );
}

export function Sidebar({ user }: { user?: { is_admin: boolean } | null }) {
  return (
    <aside className="sticky top-14 hidden h-[calc(100dvh-3.5rem)] w-[220px] shrink-0 overflow-y-auto border-r border-border bg-bg lg:block">
      <NavContent user={user} />
    </aside>
  );
}

export function MobileNav({ user }: { user?: { is_admin: boolean } | null }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        aria-expanded={open}
        className="grid size-9 place-items-center rounded-lg border border-border bg-surface text-[15px] text-muted lg:hidden"
      >
        <IconMenu />
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
          />
          <div className="animate-fade-up absolute inset-y-0 left-0 flex w-[260px] max-w-[85vw] flex-col overflow-y-auto border-r border-border bg-bg shadow-panel">
            <div className="flex items-center justify-between px-4 py-3.5">
              <span className="text-sm font-semibold">Navigation</span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="grid size-8 place-items-center rounded-lg text-muted hover:bg-bg-subtle hover:text-text"
              >
                <IconX />
              </button>
            </div>
            <NavContent onNavigate={() => setOpen(false)} user={user} />
          </div>
        </div>
      ) : null}
    </>
  );
}
