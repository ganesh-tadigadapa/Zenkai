import Link from "next/link";

import { ReviewActions } from "@/components/admin/ReviewActions";
import { CategoryBadge, CostBadge, DeadlineBadge } from "@/components/opportunity/badges";
import { Badge } from "@/components/ui/Badge";
import { IconExternal } from "@/components/ui/Icons";
import { CATEGORY_SHORT, cx, formatDate, relativeTime, titleCase } from "@/lib/format";
import type { AdminOpportunity } from "@/lib/types";

/** Confidence is the extractor's own estimate, so it is shown as a bar, not a verdict. */
function Confidence({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const tone = percent >= 80 ? "bg-verified" : percent >= 55 ? "bg-review" : "bg-expired";
  return (
    <div className="min-w-[120px]">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">
          Confidence
        </span>
        <span className="tnum text-[12px] font-semibold text-text">{percent}%</span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-bg-subtle">
        <div className={cx("h-full rounded-full", tone)} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

function Extracted({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">{label}</p>
      <p className="mt-0.5 text-[12.5px] leading-relaxed text-text">{value}</p>
    </div>
  );
}

export function ReviewCard({
  opportunity,
  reviewer,
}: {
  opportunity: AdminOpportunity;
  reviewer: string;
}) {
  return (
    <article className="rounded-panel border border-border bg-surface p-5">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-[12.5px] font-medium text-muted">{opportunity.organization.name}</p>
          <h3 className="mt-0.5 text-[15px] font-semibold leading-snug text-text">
            <Link href={`/opportunities/${opportunity.slug}`} className="hover:text-accent">
              {opportunity.title}
            </Link>
          </h3>
          <p className="mt-1.5 line-clamp-2 text-[13px] leading-relaxed text-muted">
            {opportunity.summary}
          </p>
        </div>
        <Confidence value={opportunity.confidence} />
      </header>

      <div className="mt-3.5 flex flex-wrap items-center gap-1.5">
        <CategoryBadge category={opportunity.category} />
        {titleCase(opportunity.opportunity_type) !== CATEGORY_SHORT[opportunity.category] ? (
          <Badge tone="neutral">{titleCase(opportunity.opportunity_type)}</Badge>
        ) : null}
        <CostBadge cost={opportunity.cost_type} />
        <DeadlineBadge opportunity={opportunity} />
        <Badge tone="neutral">{titleCase(opportunity.data_origin)}</Badge>
      </div>

      <div className="mt-4 grid gap-4 rounded-card border border-border bg-bg-subtle p-4 sm:grid-cols-2">
        <Extracted
          label="Extracted deadline"
          value={
            opportunity.is_rolling
              ? "Rolling — no deadline"
              : opportunity.deadline
                ? `${opportunity.deadline_is_estimated ? "≈ " : ""}${formatDate(opportunity.deadline)}`
                : "None found"
          }
        />
        <Extracted
          label="Extracted eligibility"
          value={opportunity.eligibility ?? "None found"}
        />
        <Extracted label="Detected" value={formatDate(opportunity.discovered_at)} />
        <Extracted
          label="Source"
          value={
            <a
              href={opportunity.source_url}
              target="_blank"
              rel="noopener noreferrer nofollow"
              className="inline-flex items-center gap-1 break-all text-accent hover:underline"
            >
              {opportunity.source?.name ?? new URL(opportunity.source_url).hostname}
              <IconExternal className="text-[12px]" />
            </a>
          }
        />
      </div>

      <footer className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
        <p className="text-[11.5px] text-faint">
          Last checked {relativeTime(opportunity.last_checked_at)}
          {opportunity.verified_by ? ` · previously by ${opportunity.verified_by}` : null}
        </p>
        <ReviewActions
          opportunityId={opportunity.id}
          reviewer={reviewer}
          status={opportunity.verification_status}
        />
      </footer>
    </article>
  );
}
