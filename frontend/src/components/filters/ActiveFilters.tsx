"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { IconX } from "@/components/ui/Icons";
import { titleCase } from "@/lib/format";

const LABELS: Record<string, string> = {
  q: "Search",
  category: "Category",
  credential_type: "Credential",
  specialization: "Subject",
  proctored: "Proctoring",
  assessment: "Assessment",
  level: "Level",
  delivery: "Delivery",
  issuer: "Issuer",
  type: "Type",
  cost: "Cost",
  organization: "Organisation",
  free_only: "Confirmed free",
  verified_only: "Reviewer-checked",
  remote: "Remote only",
  deadline_within_days: "Closing within",
};

const TRACKED = Object.keys(LABELS);

/** Removable chips for every applied filter, so nothing filters silently. */
export function ActiveFilters() {
  const router = useRouter();
  const params = useSearchParams();

  const chips: { key: string; value: string; label: string }[] = [];
  for (const key of TRACKED) {
    for (const value of params.getAll(key)) {
      if (!value) continue;
      const label =
        key === "deadline_within_days"
          ? `Closing within ${value} days`
          : key.endsWith("_only") || key === "remote"
            ? LABELS[key]
            : key === "q"
              // Echo the query exactly as typed; title-casing it would misquote
              // the student back to themselves.
              ? `Search: “${value}”`
              : `${LABELS[key]}: ${titleCase(value)}`;
      chips.push({ key, value, label });
    }
  }

  if (chips.length === 0) return null;

  function remove(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    const remaining = next.getAll(key).filter((item) => item !== value);
    next.delete(key);
    remaining.forEach((item) => next.append(key, item));
    next.delete("offset");
    router.push(`/opportunities?${next.toString()}`, { scroll: false });
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {chips.map((chip) => (
        <button
          key={`${chip.key}:${chip.value}`}
          type="button"
          onClick={() => remove(chip.key, chip.value)}
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface py-1 pl-2.5 pr-1.5 text-[12px] text-text transition-colors hover:border-border-strong hover:bg-bg-subtle"
        >
          {chip.label}
          <IconX className="text-[13px] text-faint" aria-hidden />
          <span className="sr-only">Remove filter</span>
        </button>
      ))}
      <button
        type="button"
        onClick={() => {
          const next = new URLSearchParams();
          const query = params.get("q");
          if (query) next.set("q", query);
          router.push(`/opportunities?${next.toString()}`, { scroll: false });
        }}
        className="ml-1 text-[12px] font-medium text-accent hover:underline"
      >
        Clear all
      </button>
    </div>
  );
}
