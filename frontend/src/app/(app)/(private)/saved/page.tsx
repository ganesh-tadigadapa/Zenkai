import type { Metadata } from "next";

import { PageHeader } from "@/components/layout/PageHeader";
import { SectionHeader } from "@/components/layout/PageHeader";
import { OpportunityGrid } from "@/components/opportunity/OpportunityGrid";
import { OpportunityRow } from "@/components/opportunity/OpportunityCard";
import { IconBookmark, IconClock } from "@/components/ui/Icons";
import { StatsCard } from "@/components/ui/StatsCard";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import type { SavedPayload } from "@/lib/types";

export const metadata: Metadata = { title: "Saved" };
export const dynamic = "force-dynamic";

export default async function SavedPage() {
  let payload: SavedPayload;
  try {
    payload = await api.saved();
  } catch (error) {
    return (
      <ErrorState
        title="Could not load your saved list"
        message={error instanceof ApiError ? error.message : undefined}
      />
    );
  }

  const closingSoon = payload.active.filter(
    (item) => item.days_left !== null && item.days_left <= 7,
  );

  if (payload.total === 0) {
    return (
      <>
        <PageHeader
          title="Saved"
          description="Opportunities you've kept for later, with their deadlines tracked."
        />
        <EmptyState
          icon={<IconBookmark />}
          title="Nothing saved yet"
          body="Use the bookmark button on any opportunity to keep it here. Saved items keep their deadline countdown where one is published, and closed ones move to their own section."
          action={{ href: "/opportunities", label: "Browse opportunities" }}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Saved"
        description="Opportunities you've kept for later, with their deadlines tracked."
      />

      <section aria-label="Summary" className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatsCard label="Saved" value={payload.total} icon={<IconBookmark />} />
        <StatsCard label="Still open" value={payload.active.length} tone="verified" />
        <StatsCard
          label="Closing this week"
          value={closingSoon.length}
          tone="critical"
          href="/deadlines"
          icon={<IconClock />}
        />
        <StatsCard label="Expired" value={payload.expired.length} />
      </section>

      <section className="pb-10">
        <SectionHeader
          title="Still open"
          description="Sorted by how soon each one closes, where a deadline is published."
        />
        <OpportunityGrid
          opportunities={payload.active}
          emptyTitle="Nothing open on your list"
          emptyBody="Everything you saved has passed its deadline. Browse the catalogue to find more."
        />
      </section>

      {payload.expired.length > 0 ? (
        <section className="border-t border-border pt-8">
          <SectionHeader
            title="Expired"
            description="Past their deadline, or marked closed by a reviewer. Kept for your reference."
          />
          <div className="space-y-2 opacity-70">
            {payload.expired.map((opportunity) => (
              <OpportunityRow key={opportunity.id} opportunity={opportunity} />
            ))}
          </div>
        </section>
      ) : null}
    </>
  );
}
