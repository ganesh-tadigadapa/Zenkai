import { OpportunityCard } from "@/components/opportunity/OpportunityCard";
import { EmptyState } from "@/components/ui/States";
import { cx } from "@/lib/format";
import type { Opportunity } from "@/lib/types";

export function OpportunityGrid({
  opportunities,
  showMatch = true,
  columns = 3,
  emptyTitle = "No opportunities match",
  emptyBody = "Try widening your filters or clearing the search.",
  className,
}: {
  opportunities: Opportunity[];
  showMatch?: boolean;
  columns?: 2 | 3;
  emptyTitle?: string;
  emptyBody?: string;
  className?: string;
}) {
  if (opportunities.length === 0) {
    return <EmptyState title={emptyTitle} body={emptyBody} />;
  }

  return (
    <div
      className={cx(
        "grid gap-4",
        // The feed sits beside a filter rail, so the third column only earns its
        // place on genuinely wide screens — otherwise cards get too narrow to
        // hold a title and its badges on one line each.
        columns === 3 ? "sm:grid-cols-2 2xl:grid-cols-3" : "sm:grid-cols-2",
        className,
      )}
    >
      {opportunities.map((opportunity) => (
        <OpportunityCard
          key={opportunity.id}
          opportunity={opportunity}
          showMatch={showMatch}
        />
      ))}
    </div>
  );
}
