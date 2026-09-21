"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

const OPTIONS = [
  { value: "deadline", label: "Closing soonest" },
  { value: "relevance", label: "Best match" },
  { value: "newest", label: "Newest first" },
  { value: "updated", label: "Recently updated" },
  { value: "title", label: "A–Z" },
];

export function SortSelect() {
  const router = useRouter();
  const params = useSearchParams();
  const [, startTransition] = useTransition();

  function onChange(value: string) {
    const next = new URLSearchParams(params.toString());
    next.set("sort", value);
    next.delete("offset");
    startTransition(() => router.push(`/opportunities?${next.toString()}`, { scroll: false }));
  }

  return (
    <label className="inline-flex items-center gap-2 text-[12.5px] text-muted">
      <span className="hidden sm:inline">Sort</span>
      <select
        value={params.get("sort") ?? "deadline"}
        onChange={(event) => onChange(event.target.value)}
        aria-label="Sort opportunities"
        className="h-9 rounded-lg border border-border bg-surface px-2.5 text-[13px] text-text focus:border-accent focus:outline-none"
      >
        {OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
