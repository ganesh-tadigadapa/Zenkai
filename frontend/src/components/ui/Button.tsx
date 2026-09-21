import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

import { cx } from "@/lib/format";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-accent text-white border-transparent hover:bg-accent-hover shadow-card disabled:bg-faint",
  secondary:
    "bg-surface text-text border-border-strong hover:bg-bg-subtle hover:border-faint",
  ghost: "bg-transparent text-muted border-transparent hover:bg-bg-subtle hover:text-text",
  danger: "bg-transparent text-expired border-border hover:bg-expired-soft hover:border-expired",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px] gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-12 px-6 text-[15px] gap-2",
};

const BASE = cx(
  "inline-flex items-center justify-center rounded-[10px] border font-medium",
  "transition-[background-color,border-color,color,box-shadow] duration-150",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

export function Button({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ComponentProps<"button"> & { variant?: Variant; size?: Size }) {
  return <button className={cx(BASE, VARIANTS[variant], SIZES[size], className)} {...props} />;
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ComponentProps<typeof Link> & { variant?: Variant; size?: Size; children: ReactNode }) {
  return (
    <Link className={cx(BASE, VARIANTS[variant], SIZES[size], className)} {...props}>
      {children}
    </Link>
  );
}
