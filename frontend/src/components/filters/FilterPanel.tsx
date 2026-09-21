"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState, useTransition } from "react";

import { IconFilter, IconX } from "@/components/ui/Icons";
import { cx } from "@/lib/format";
import type { Facets } from "@/lib/types";

/**
 * Filters live in the URL, so every filtered view is shareable, bookmarkable
 * and restorable on refresh. The panel only ever rewrites search params.
 */
const GROUPS: { param: string; label: string; facet: string }[] = [
  { param: "category", label: "Category", facet: "category" },
  // Credential facets. Only rendered when the API reports counts for them, so
  // they stay out of the way until the catalogue has the data.
  { param: "credential_type", label: "Credential", facet: "credential_type" },
  { param: "proctored", label: "Proctoring", facet: "proctored" },
  { param: "assessment", label: "Assessment", facet: "assessment" },
  { param: "level", label: "Level", facet: "level" },
  { param: "delivery", label: "Delivery", facet: "delivery" },
  { param: "type", label: "Type", facet: "type" },
  { param: "cost", label: "Cost", facet: "cost" },
  { param: "organization", label: "Organisation", facet: "organization" },
];

/*
  Each hint says what the filter *excludes*, not just what it includes. Most of
  the catalogue has an unconfirmed cost, so "Free only" hides the majority —
  correct, because an unstated price is not a free one, but useless to a
  student unless the control admits it.
*/
const TOGGLES: { param: string; label: string; hint: string }[] = [
  {
    param: "free_only",
    label: "Confirmed free",
    hint: "Hides anything whose cost the provider hasn't stated",
  },
  {
    param: "verified_only",
    label: "Checked by a reviewer",
    hint: "Hides records still awaiting verification",
  },
  { param: "remote", label: "Remote only", hint: "Can be done from anywhere" },
];

const DEADLINE_OPTIONS = [
  { value: "", label: "Any time" },
  { value: "7", label: "Next 7 days" },
  { value: "14", label: "Next 14 days" },
  { value: "30", label: "Next 30 days" },
  { value: "90", label: "Next 3 months" },
];

export function FilterPanel({ facets }: { facets: Facets }) {
  const router = useRouter();
  const params = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [open, setOpen] = useState(false);

  const push = useCallback(
    (next: URLSearchParams) => {
      next.delete("offset"); // any filter change returns to the first page
      startTransition(() => {
        router.push(`/opportunities?${next.toString()}`, { scroll: false });
      });
    },
    [router],
  );

  function toggleValue(param: string, value: string) {
    const next = new URLSearchParams(params.toString());
    const current = next.getAll(param);
    next.delete(param);
    const updated = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];
    updated.forEach((item) => next.append(param, item));
    push(next);
  }

  function setFlag(param: string, on: boolean) {
    const next = new URLSearchParams(params.toString());
    if (on) next.set(param, "true");
    else next.delete(param);
    push(next);
  }

  function setSingle(param: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(param, value);
    else next.delete(param);
    push(next);
  }

  function clearAll() {
    const next = new URLSearchParams();
    const query = params.get("q");
    if (query) next.set("q", query);
    push(next);
  }

  const activeCount =
    GROUPS.reduce((total, group) => total + params.getAll(group.param).length, 0) +
    TOGGLES.filter((toggle) => params.get(toggle.param) === "true").length +
    (params.get("deadline_within_days") ? 1 : 0);

  const body = (
    <div className={cx("space-y-6", isPending && "opacity-60")}>
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">
          Quick filters
        </p>
        <div className="space-y-1.5">
          {TOGGLES.map((toggle) => {
            const checked = params.get(toggle.param) === "true";
            return (
              <label
                key={toggle.param}
                className="flex cursor-pointer items-start gap-2.5 rounded-lg px-1.5 py-1 hover:bg-bg-subtle"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(event) => setFlag(toggle.param, event.target.checked)}
                  className="mt-0.5 size-3.5 shrink-0 accent-[var(--accent)]"
                />
                <span className="min-w-0">
                  <span className="block text-[13px] font-medium text-text">{toggle.label}</span>
                  <span className="block text-[11.5px] text-faint">{toggle.hint}</span>
                </span>
              </label>
            );
          })}
        </div>
      </div>

      <div>
        <label
          htmlFor="deadline-filter"
          className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.07em] text-faint"
        >
          Deadline
        </label>
        <select
          id="deadline-filter"
          value={params.get("deadline_within_days") ?? ""}
          onChange={(event) => setSingle("deadline_within_days", event.target.value)}
          className="h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-[13px] text-text focus:border-accent focus:outline-none"
        >
          {DEADLINE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {GROUPS.map((group) => {
        const values = facets[group.facet] ?? [];
        if (values.length === 0) return null;
        const selected = params.getAll(group.param);
        return (
          <fieldset key={group.param}>
            <legend className="mb-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">
              {group.label}
            </legend>
            <div
              className={cx(
                "space-y-0.5",
                values.length > 8 && "max-h-56 overflow-y-auto pr-1",
              )}
            >
              {values.map((value) => {
                const checked = selected.includes(value.value);
                return (
                  <label
                    key={value.value}
                    className="flex cursor-pointer items-center gap-2.5 rounded-lg px-1.5 py-[5px] hover:bg-bg-subtle"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleValue(group.param, value.value)}
                      className="size-3.5 shrink-0 accent-[var(--accent)]"
                    />
                    <span className="min-w-0 flex-1 truncate text-[13px] text-text">
                      {value.label}
                    </span>
                    <span className="tnum shrink-0 text-[11px] text-faint">{value.count}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        );
      })}
    </div>
  );

  return (
    <>
      {/* Mobile trigger */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mb-4 inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-surface px-3 text-[13px] font-medium text-text lg:hidden"
      >
        <IconFilter />
        Filters
        {activeCount > 0 ? (
          <span className="tnum grid size-4 place-items-center rounded-full bg-accent text-[10px] font-semibold text-white">
            {activeCount}
          </span>
        ) : null}
      </button>

      {/* Desktop panel */}
      <aside className="hidden w-[228px] shrink-0 lg:block">
        <div className="sticky top-[4.75rem]">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-[13px] font-semibold text-text">Filters</h2>
            {activeCount > 0 ? (
              <button
                type="button"
                onClick={clearAll}
                className="text-[12px] font-medium text-accent hover:underline"
              >
                Clear all
              </button>
            ) : null}
          </div>
          {body}
        </div>
      </aside>

      {/* Mobile drawer */}
      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close filters"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
          />
          <div className="animate-fade-up absolute inset-x-0 bottom-0 max-h-[85dvh] overflow-y-auto rounded-t-2xl border-t border-border bg-bg p-5 shadow-panel">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Filters</h2>
              <div className="flex items-center gap-3">
                {activeCount > 0 ? (
                  <button type="button" onClick={clearAll} className="text-[12px] text-accent">
                    Clear all
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label="Close filters"
                  className="grid size-8 place-items-center rounded-lg text-muted hover:bg-bg-subtle"
                >
                  <IconX />
                </button>
              </div>
            </div>
            {body}
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="mt-6 h-11 w-full rounded-[10px] bg-accent text-sm font-medium text-white"
            >
              Show results
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}
