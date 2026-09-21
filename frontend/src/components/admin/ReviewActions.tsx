"use client";

import { useState, useTransition } from "react";

import { Button } from "@/components/ui/Button";
import { IconCheck, IconX } from "@/components/ui/Icons";
import { reviewAction } from "@/lib/actions";
import { cx } from "@/lib/format";

/**
 * Approve / reject controls. Rejection asks for a note first: a rejected record
 * is hidden from students, so the audit trail should say why.
 */
export function ReviewActions({
  opportunityId,
  reviewer,
  status,
}: {
  opportunityId: string;
  reviewer: string;
  status: string;
}) {
  const [isPending, startTransition] = useTransition();
  const [feedback, setFeedback] = useState<{ ok: boolean; message: string } | null>(null);
  const [rejecting, setRejecting] = useState(false);
  const [notes, setNotes] = useState("");

  function run(action: "approve" | "reject") {
    startTransition(async () => {
      const result = await reviewAction(opportunityId, action, reviewer, notes || undefined);
      setFeedback({ ok: result.ok, message: result.message ?? "Done." });
      if (result.ok) {
        setRejecting(false);
        setNotes("");
      }
    });
  }

  if (feedback?.ok) {
    return (
      <p className="inline-flex items-center gap-1.5 text-[12.5px] font-medium text-verified">
        <IconCheck />
        {feedback.message}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {rejecting ? (
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Why is this being rejected?"
            aria-label="Rejection reason"
            className="h-9 flex-1 rounded-lg border border-border bg-surface px-3 text-[13px] text-text placeholder:text-faint focus:border-accent focus:outline-none"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="danger"
              onClick={() => run("reject")}
              disabled={isPending || notes.trim().length === 0}
            >
              Confirm reject
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setRejecting(false)} disabled={isPending}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {status !== "verified" ? (
            <Button size="sm" onClick={() => run("approve")} disabled={isPending}>
              <IconCheck />
              Approve
            </Button>
          ) : null}
          {status !== "rejected" ? (
            <Button size="sm" variant="danger" onClick={() => setRejecting(true)} disabled={isPending}>
              <IconX />
              Reject
            </Button>
          ) : null}
        </div>
      )}

      {feedback && !feedback.ok ? (
        <p className={cx("text-[12px] text-expired")} role="alert">
          {feedback.message}
        </p>
      ) : null}
    </div>
  );
}
