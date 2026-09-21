import { Badge, Dot } from "@/components/ui/Badge";
import { IconGlobe, IconSparkles } from "@/components/ui/Icons";

/**
 * Illustrative cards for the hero. These are explicitly labelled as examples —
 * they are not drawn from the catalogue and must never look like live records.
 */
export function PreviewCard({
  organization,
  title,
  category,
  cost,
  deadline,
  urgent = false,
  isNew = false,
  className,
  style,
}: {
  organization: string;
  title: string;
  category: string;
  cost: string;
  deadline: string;
  urgent?: boolean;
  isNew?: boolean;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      aria-hidden
      className={`w-[268px] rounded-panel border border-border bg-surface p-4 shadow-float ${className ?? ""}`}
      style={style}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-[12px] font-medium text-muted">{organization}</p>
          <p className="mt-0.5 text-[13.5px] font-semibold leading-snug text-text">{title}</p>
        </div>
        {isNew ? (
          <span className="shrink-0 rounded-md bg-accent px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
            New
          </span>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <Badge tone="neutral">
          <IconSparkles />
          {category}
        </Badge>
        <Badge tone="verified">{cost}</Badge>
        <Badge tone={urgent ? "critical" : "calm"} className="tnum">
          {deadline}
        </Badge>
      </div>

      <div className="mt-3.5 flex items-center justify-between gap-2 border-t border-border pt-3">
        <span className="inline-flex items-center gap-1.5 text-[11.5px] text-faint">
          <IconGlobe />
          Remote
        </span>
        <Badge tone="verified">
          <Dot className="bg-verified" />
          Verified
        </Badge>
      </div>
    </div>
  );
}
