"use client";

import { useFormStatus } from "react-dom";

import { Button } from "@/components/ui/Button";
import { guestAction } from "@/lib/actions";

function Submit({
  children,
  variant,
  size,
  className,
}: {
  children: React.ReactNode;
  variant: "primary" | "secondary" | "ink";
  size: "sm" | "md" | "lg";
  className?: string;
}) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" variant={variant} size={size} disabled={pending} className={className}>
      {pending ? "Starting…" : children}
    </Button>
  );
}

/**
 * One click into the app on a fresh guest account — no email, no password.
 *
 * A form rather than a link, so creating the account is a POST and cannot be
 * triggered by a prefetch or a crawler following links.
 */
export function GuestButton({
  next,
  children = "Continue as guest",
  variant = "primary",
  size = "lg",
  className,
}: {
  next?: string;
  children?: React.ReactNode;
  variant?: "primary" | "secondary" | "ink";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  return (
    <form action={guestAction} className="contents">
      {next ? <input type="hidden" name="next" value={next} /> : null}
      <Submit variant={variant} size={size} className={className}>
        {children}
      </Submit>
    </form>
  );
}
