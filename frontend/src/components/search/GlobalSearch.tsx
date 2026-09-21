"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { IconSearch } from "@/components/ui/Icons";

/**
 * Header search. Submits to /opportunities rather than searching in place, so
 * results always land on the full feed with its filters available.
 */
export function GlobalSearch({ autoFocus = false }: { autoFocus?: boolean }) {
  const router = useRouter();
  const params = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);

  // Derive from the URL during render rather than syncing in an effect: when
  // navigation changes ?q=, the field follows without an extra render pass.
  const queryFromUrl = params.get("q") ?? "";
  const [lastQuery, setLastQuery] = useState(queryFromUrl);
  const [value, setValue] = useState(queryFromUrl);
  if (queryFromUrl !== lastQuery) {
    setLastQuery(queryFromUrl);
    setValue(queryFromUrl);
  }

  // "/" focuses search, the convention in developer tools.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const typingElsewhere =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable);
      if (event.key === "/" && !typingElsewhere) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = value.trim();
    router.push(trimmed ? `/opportunities?q=${encodeURIComponent(trimmed)}` : "/opportunities");
  }

  return (
    <form onSubmit={onSubmit} role="search" className="relative">
      <label htmlFor="global-search" className="sr-only">
        Search opportunities
      </label>
      <IconSearch className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[15px] text-faint" />
      <input
        id="global-search"
        ref={inputRef}
        type="search"
        autoFocus={autoFocus}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Search certifications, internships, credits…"
        className="h-9 w-full rounded-lg border border-border bg-bg-subtle pl-9 pr-10 text-[13px] text-text placeholder:text-faint focus:border-accent focus:bg-surface focus:outline-none"
      />
      <kbd className="pointer-events-none absolute right-2.5 top-1/2 hidden -translate-y-1/2 rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] text-faint lg:block">
        /
      </kbd>
    </form>
  );
}
