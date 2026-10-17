import { IconCheck, IconShield } from "@/components/ui/Icons";
import { delay } from "@/lib/style";

/** Feature card art: records traced back to their official page. */
export function SourcesVisual() {
  return (
    <div className="relative grid h-full place-items-center">
      {[0, 1200, 2400].map((ms) => (
        <span
          key={ms}
          className="hero-ring !w-[220px] !border-accent/40"
          style={{ ...delay(ms), animationDuration: "3.6s" }}
        />
      ))}
      <span className="relative grid size-14 place-items-center rounded-2xl border border-border-strong bg-surface text-[22px] text-accent shadow-[var(--shadow-md)]">
        <IconShield />
      </span>
      <span
        className="animate-float absolute left-[14%] top-[22%] rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] text-muted shadow-[var(--shadow-sm)]"
        style={delay(0)}
      >
        devpost.com
      </span>
      <span
        className="animate-float absolute bottom-[18%] right-[10%] inline-flex items-center gap-1 rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] text-muted shadow-[var(--shadow-sm)]"
        style={delay(1500)}
      >
        <IconCheck className="text-verified" />
        Official page
      </span>
    </div>
  );
}
