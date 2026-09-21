"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { IconShield, IconUser } from "@/components/ui/Icons";
import { logoutAction } from "@/lib/actions";
import { cx } from "@/lib/format";
import type { Profile } from "@/lib/types";

export function UserMenu({ user }: { user: Profile }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const initials = user.name
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  // Close on outside click and on Escape — both expected of a menu.
  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Account menu for ${user.name}`}
        className="grid size-9 shrink-0 place-items-center rounded-full border border-border bg-bg-subtle text-[11px] font-semibold text-muted transition-colors hover:border-border-strong hover:text-text"
      >
        {initials || <IconUser />}
      </button>

      {open ? (
        <div
          role="menu"
          className="animate-fade-up absolute right-0 top-[calc(100%+8px)] z-50 w-60 overflow-hidden rounded-panel border border-border bg-surface shadow-panel"
        >
          <div className="border-b border-border px-3.5 py-3">
            <p className="truncate text-[13px] font-semibold text-text">{user.name}</p>
            <p className="truncate text-[12px] text-muted">{user.email}</p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {user.is_admin ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-accent-soft px-1.5 py-0.5 text-[10.5px] font-medium text-accent">
                  <IconShield className="text-[11px]" />
                  Reviewer
                </span>
              ) : null}
              {user.is_demo ? (
                <span className="rounded-md bg-bg-subtle px-1.5 py-0.5 text-[10.5px] font-medium text-faint">
                  Demo account
                </span>
              ) : null}
            </div>
          </div>

          <div className="p-1">
            <Link
              href="/profile"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block rounded-lg px-2.5 py-2 text-[13px] text-muted transition-colors hover:bg-bg-subtle hover:text-text"
            >
              Profile and preferences
            </Link>
            <Link
              href="/saved"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block rounded-lg px-2.5 py-2 text-[13px] text-muted transition-colors hover:bg-bg-subtle hover:text-text"
            >
              Saved opportunities
            </Link>
          </div>

          <form action={logoutAction} className="border-t border-border p-1">
            <button
              type="submit"
              role="menuitem"
              className={cx(
                "w-full rounded-lg px-2.5 py-2 text-left text-[13px] font-medium",
                "text-muted transition-colors hover:bg-bg-subtle hover:text-text",
              )}
            >
              Sign out
            </button>
          </form>
        </div>
      ) : null}
    </div>
  );
}
