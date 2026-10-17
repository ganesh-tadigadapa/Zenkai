import { IconClock } from "@/components/ui/Icons";
import { delay } from "@/lib/style";

/** Feature card art: a deadline dial running down. */
export function DeadlineVisual() {
  return (
    <div className="relative grid h-full place-items-center">
      <svg viewBox="0 0 120 120" className="size-32 -rotate-90" aria-hidden>
        <circle cx="60" cy="60" r="48" fill="none" stroke="var(--border)" strokeWidth="6" />
        <circle
          className="dial"
          cx="60"
          cy="60"
          r="48"
          fill="none"
          stroke="var(--accent)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray="90 211.6"
        />
      </svg>
      <span className="absolute grid place-items-center text-[24px] text-text">
        <IconClock />
      </span>
      <span
        className="animate-float absolute right-[8%] top-[20%] rounded-full border border-critical/30 bg-critical-soft px-2.5 py-1 text-[11px] font-medium text-critical"
        style={delay(800)}
      >
        Closes soon
      </span>
    </div>
  );
}
