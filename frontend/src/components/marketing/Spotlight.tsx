"use client";

import { useRef } from "react";

import { cx } from "@/lib/format";

/**
 * A soft glow that follows the pointer across its children.
 *
 * The position is written straight to CSS variables rather than React state,
 * so moving the mouse never re-renders anything. Touch screens simply never
 * see the glow.
 */
export function Spotlight({
  children,
  className,
  size = 420,
  strength = 14,
}: {
  children: React.ReactNode;
  className?: string;
  /** Glow radius in pixels. */
  size?: number;
  /** Accent mix in percent at the centre of the glow. */
  strength?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (event.pointerType !== "mouse") return;
    const element = ref.current;
    if (!element) return;
    const rect = element.getBoundingClientRect();
    element.style.setProperty("--x", `${event.clientX - rect.left}px`);
    element.style.setProperty("--y", `${event.clientY - rect.top}px`);
  }

  return (
    <div ref={ref} onPointerMove={onPointerMove} className={cx("group/spot relative", className)}>
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-500 group-hover/spot:opacity-100"
        style={{
          background: `radial-gradient(${size}px circle at var(--x, 50%) var(--y, 50%), color-mix(in srgb, var(--accent) ${strength}%, transparent), transparent 70%)`,
        }}
      />
      {children}
    </div>
  );
}
