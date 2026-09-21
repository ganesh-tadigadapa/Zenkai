"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/Button";
import { IconAlert, IconCheck } from "@/components/ui/Icons";
import { changePasswordAction, type ActionResult } from "@/lib/actions";
import { cx } from "@/lib/format";
import type { Profile } from "@/lib/types";

const inputClass =
  "h-10 w-full rounded-lg border border-border bg-surface px-3 text-[13.5px] text-text placeholder:text-faint focus:border-accent focus:outline-none";

export function AccountPanel({ user }: { user: Profile }) {
  const [state, formAction, isPending] = useActionState<ActionResult | null, FormData>(
    async (_previous, formData) => changePasswordAction(formData),
    null,
  );

  return (
    <section className="rounded-panel border border-border bg-surface p-5 sm:p-6">
      <h2 className="text-[13px] font-semibold text-text">Account</h2>
      <p className="mb-4 text-[12.5px] leading-relaxed text-muted">
        Signed in as <span className="font-medium text-text">{user.email}</span>
        {user.is_demo ? " — the seeded demo account." : null}
      </p>

      <form action={formAction} className="space-y-4 border-t border-border pt-4">
        <p className="text-[13px] font-medium text-text">Change password</p>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label
              htmlFor="current_password"
              className="mb-1.5 block text-[13px] font-medium text-text"
            >
              Current password
            </label>
            <input
              id="current_password"
              name="current_password"
              type="password"
              required
              autoComplete="current-password"
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="new_password" className="mb-1.5 block text-[13px] font-medium text-text">
              New password
            </label>
            <input
              id="new_password"
              name="new_password"
              type="password"
              required
              autoComplete="new-password"
              placeholder="At least 10 characters"
              className={inputClass}
            />
          </div>
          <div>
            <label
              htmlFor="confirm_password"
              className="mb-1.5 block text-[13px] font-medium text-text"
            >
              Confirm new password
            </label>
            <input
              id="confirm_password"
              name="confirm_password"
              type="password"
              required
              autoComplete="new-password"
              className={inputClass}
            />
          </div>
        </div>

        <p className="text-[11.5px] leading-relaxed text-faint">
          Changing your password signs out every other device. You stay signed in here.
        </p>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" variant="secondary" size="sm" disabled={isPending}>
            {isPending ? "Changing…" : "Change password"}
          </Button>
          {state ? (
            <p
              role="status"
              className={cx(
                "inline-flex items-center gap-1.5 text-[12.5px]",
                state.ok ? "text-verified" : "text-expired",
              )}
            >
              {state.ok ? <IconCheck /> : <IconAlert />}
              {state.message}
            </p>
          ) : null}
        </div>
      </form>
    </section>
  );
}
