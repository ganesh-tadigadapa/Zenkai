import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { OpportunityRow } from "@/components/opportunity/OpportunityCard";
import { IconClock } from "@/components/ui/Icons";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import { cx } from "@/lib/format";
import type { DeadlinesPayload, Opportunity } from "@/lib/types";

export const metadata: Metadata = { title: "Deadlines" };
export const dynamic = "force-dynamic";

/**
 * Urgency is carried by a single coloured rail per group rather than by
 * shouting on every row, so the page stays scannable instead of alarming.
 */
function Group({
  title,
  caption,
  tone,
  opportunities,
}: {
  title: string;
  caption: string;
  tone: "critical" | "soon" | "calm";
  opportunities: Opportunity[];
}) {
  if (opportunities.length === 0) return null;

  const rail = {
    critical: "bg-critical",
    soon: "bg-soon",
    calm: "bg-border-strong",
  }[tone];

  const count = {
    critical: "bg-critical-soft text-critical",
    soon: "bg-soon-soft text-soon",
    calm: "bg-calm-soft text-calm",
  }[tone];

  return (
    <section className="relative pl-5">
      <span aria-hidden className={cx("absolute left-0 top-1.5 h-[calc(100%-0.5rem)] w-[3px] rounded-full", rail)} />
      <div className="mb-3 flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
        <h2 className="text-[15px] font-semibold tracking-[-0.01em] text-text">{title}</h2>
        <span className={cx("tnum rounded-md px-1.5 py-0.5 text-[11px] font-semibold", count)}>
          {opportunities.length}
        </span>
        <p className="text-[12.5px] text-muted">{caption}</p>
      </div>
      <div className="space-y-2">
        {opportunities.map((opportunity) => (
          <OpportunityRow key={opportunity.id} opportunity={opportunity} />
        ))}
      </div>
    </section>
  );
}

export default async function DeadlinesPage({
  searchParams,
}: {
  searchParams: Promise<{ saved_only?: string }>;
}) {
  const params = await searchParams;
  const savedOnly = params.saved_only === "true";

  let payload: DeadlinesPayload;
  try {
    payload = await api.deadlines({ horizon_days: 90, saved_only: savedOnly });
  } catch (error) {
    return (
      <ErrorState
        title="Could not load deadlines"
        message={error instanceof ApiError ? error.message : undefined}
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Deadlines"
        description="Opportunities whose official source publishes a deadline, closest first."
        actions={
          <div className="flex rounded-lg border border-border bg-surface p-0.5 text-[12.5px] font-medium">
            <Link
              href="/deadlines"
              className={cx(
                "rounded-[7px] px-3 py-1.5 transition-colors",
                savedOnly ? "text-muted hover:text-text" : "bg-bg-subtle text-text",
              )}
            >
              All
            </Link>
            <Link
              href="/deadlines?saved_only=true"
              className={cx(
                "rounded-[7px] px-3 py-1.5 transition-colors",
                savedOnly ? "bg-bg-subtle text-text" : "text-muted hover:text-text",
              )}
            >
              Saved only
            </Link>
          </div>
        }
      />

      {payload.total === 0 ? (
        <EmptyState
          icon={<IconClock />}
          title={savedOnly ? "No deadlines on your saved list" : "No published deadlines yet"}
          body={
            savedOnly
              ? "Save an opportunity that publishes a deadline and it will be tracked here."
              : "Zenkai shows a date only where the official source publishes one, and never invents a cycle from a programme's history. Most of today's curated catalogue is either continuously open or announces dates each cycle, so there is nothing to count down yet. This fills in as source checking is rolled out."
          }
          action={{ href: "/opportunities", label: "Browse opportunities" }}
        />
      ) : (
        <div className="space-y-10">
          <Group
            title="Closing today"
            caption="Last chance to apply."
            tone="critical"
            opportunities={payload.today}
          />
          <Group
            title="This week"
            caption="Closing within the next seven days."
            tone="soon"
            opportunities={payload.this_week}
          />
          <Group
            title="Upcoming"
            caption="Further out — worth preparing for."
            tone="calm"
            opportunities={payload.upcoming}
          />
        </div>
      )}
    </>
  );
}
