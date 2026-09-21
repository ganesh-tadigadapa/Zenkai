"use client";

import Link from "next/link";
import { useActionState } from "react";

import { Button } from "@/components/ui/Button";
import { IconAlert } from "@/components/ui/Icons";
import { loginAction, signupAction, type ActionResult } from "@/lib/actions";
import { cx } from "@/lib/format";

const inputClass =
  "h-11 w-full rounded-[10px] border border-border bg-surface px-3.5 text-[14px] text-text placeholder:text-faint focus:border-accent focus:outline-none";

function Field({
  id,
  label,
  type = "text",
  autoComplete,
  placeholder,
  hint,
  required = true,
}: {
  id: string;
  label: string;
  type?: string;
  autoComplete?: string;
  placeholder?: string;
  hint?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-[13px] font-medium text-text">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        required={required}
        autoComplete={autoComplete}
        placeholder={placeholder}
        aria-describedby={hint ? `${id}-hint` : undefined}
        className={inputClass}
      />
      {hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-[11.5px] text-faint">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function AuthForm({
  mode,
  next,
  expired = false,
}: {
  mode: "login" | "signup";
  next?: string;
  /** True when the visitor arrived holding a session that no longer resolves. */
  expired?: boolean;
}) {
  const isSignup = mode === "signup";

  const [state, formAction, isPending] = useActionState<ActionResult | null, FormData>(
    async (_previous, formData) => (isSignup ? signupAction(formData) : loginAction(formData)),
    null,
  );

  return (
    <div>
      <h1 className="text-[22px] font-semibold tracking-[-0.02em] text-text">
        {isSignup ? "Create your account" : "Welcome back"}
      </h1>
      <p className="mt-1.5 text-[13.5px] leading-relaxed text-muted">
        {isSignup
          ? "Your profile drives what Zenkai surfaces, and your saved list stays yours."
          : "Sign in to your saved opportunities and matches."}
      </p>

      {expired ? (
        <p
          role="status"
          className="mt-5 rounded-[10px] border border-review/30 bg-review-soft px-3 py-2.5 text-[12.5px] leading-relaxed text-review"
        >
          Your session has ended. Sign in again to pick up where you left off.
        </p>
      ) : null}

      <form action={formAction} className="mt-7 space-y-4">
        {next ? <input type="hidden" name="next" value={next} /> : null}

        {isSignup ? (
          <Field id="name" label="Name" autoComplete="name" placeholder="Aarav Sharma" />
        ) : null}

        <Field
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@university.edu"
        />

        <Field
          id="password"
          label="Password"
          type="password"
          autoComplete={isSignup ? "new-password" : "current-password"}
          placeholder={isSignup ? "At least 10 characters" : undefined}
          hint={isSignup ? "At least 10 characters. Longer beats complicated." : undefined}
        />

        {state && !state.ok ? (
          <p
            role="alert"
            className="flex items-start gap-2 rounded-[10px] border border-expired/30 bg-expired-soft px-3 py-2.5 text-[12.5px] leading-relaxed text-expired"
          >
            <IconAlert className="mt-[2px] shrink-0" />
            {state.message}
          </p>
        ) : null}

        <Button type="submit" disabled={isPending} className="w-full" size="lg">
          {isPending
            ? isSignup
              ? "Creating account…"
              : "Signing in…"
            : isSignup
              ? "Create account"
              : "Sign in"}
        </Button>
      </form>

      <p className={cx("mt-6 text-center text-[13px] text-muted")}>
        {isSignup ? "Already have an account? " : "New to Zenkai? "}
        <Link
          href={isSignup ? "/login" : "/signup"}
          className="font-medium text-accent hover:underline"
        >
          {isSignup ? "Sign in" : "Create one"}
        </Link>
      </p>
    </div>
  );
}
