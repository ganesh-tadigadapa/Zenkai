import type { CSSProperties } from "react";

/** Entrance delay for an `.animate-blur-in` element, or any `--d` consumer. */
export const delay = (ms: number) => ({ "--d": `${ms}ms` }) as CSSProperties;

/** Types a set of CSS custom properties for a `style` prop. */
export const vars = (values: Record<string, string | number>) => values as CSSProperties;
