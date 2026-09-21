"use client";

import { useOptimistic, useState, useTransition } from "react";

import { IconBookmark } from "@/components/ui/Icons";
import { toggleSaveAction } from "@/lib/actions";
import { cx } from "@/lib/format";

export function SaveButton({
  opportunityId,
  saved,
  variant = "icon",
}: {
  opportunityId: string;
  saved: boolean;
  variant?: "icon" | "full";
}) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  // Flip immediately, then reconcile with the server response.
  const [optimisticSaved, setOptimisticSaved] = useOptimistic(saved);

  function onClick() {
    setError(null);
    startTransition(async () => {
      setOptimisticSaved(!optimisticSaved);
      const result = await toggleSaveAction(opportunityId, optimisticSaved);
      if (!result.ok) setError(result.message ?? "Could not save.");
    });
  }

  const label = optimisticSaved ? "Remove from saved" : "Save opportunity";

  if (variant === "full") {
    return (
      <button
        type="button"
        onClick={onClick}
        disabled={isPending}
        aria-pressed={optimisticSaved}
        title={error ?? label}
        className={cx(
          "inline-flex h-10 items-center justify-center gap-2 rounded-[10px] border px-4 text-sm font-medium",
          "transition-colors duration-150 disabled:opacity-60",
          optimisticSaved
            ? "border-accent bg-accent-soft text-accent"
            : "border-border-strong bg-surface text-text hover:bg-bg-subtle",
        )}
      >
        <IconBookmark className={optimisticSaved ? "fill-current" : undefined} />
        {optimisticSaved ? "Saved" : "Save"}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isPending}
      aria-label={label}
      aria-pressed={optimisticSaved}
      title={error ?? label}
      className={cx(
        "grid size-8 place-items-center rounded-lg border text-[15px] transition-colors duration-150",
        "disabled:opacity-60",
        optimisticSaved
          ? "border-accent/40 bg-accent-soft text-accent"
          : "border-transparent text-faint hover:border-border hover:bg-bg-subtle hover:text-text",
      )}
    >
      <IconBookmark className={optimisticSaved ? "fill-current" : undefined} />
    </button>
  );
}
