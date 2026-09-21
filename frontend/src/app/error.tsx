"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { IconAlert } from "@/components/ui/Icons";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Zenkai render error:", error);
  }, [error]);

  return (
    <div className="grid min-h-[60dvh] place-items-center px-4">
      <div
        role="alert"
        className="w-full max-w-md rounded-panel border border-expired/30 bg-expired-soft p-6 text-center"
      >
        <span className="mx-auto mb-3 grid size-11 place-items-center rounded-full bg-surface text-[18px] text-expired shadow-card">
          <IconAlert />
        </span>
        <h1 className="text-[15px] font-semibold text-text">Something went wrong</h1>
        <p className="mt-2 text-[13px] leading-relaxed text-muted">
          The page could not be rendered. The most common cause in development is the Zenkai API
          not running on the configured NEXT_PUBLIC_API_URL.
        </p>
        {error.digest ? (
          <p className="mt-2 font-mono text-[11px] text-faint">Reference: {error.digest}</p>
        ) : null}
        <Button onClick={reset} className="mt-5">
          Try again
        </Button>
      </div>
    </div>
  );
}
