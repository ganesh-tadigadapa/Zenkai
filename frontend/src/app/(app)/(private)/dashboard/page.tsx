import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { Shelf } from "@/components/opportunity/Shelf";
import { ButtonLink } from "@/components/ui/Button";
import {
  IconBolt,
  IconBookmark,
  IconClock,
  IconRadar,
  IconSparkles,
} from "@/components/ui/Icons";
import { StatsCard } from "@/components/ui/StatsCard";
import { ErrorState } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import { BRAND } from "@/lib/brand";

export const metadata: Metadata = { title: "Overview" };
export const dynamic = "force-dynamic";

function greeting(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default async function DashboardPage() {
  let payload;
  let profileName = "Student";

  try {
    const [dashboard, profile] = await Promise.all([
      api.dashboard(6),
      api.profile().catch(() => null),
    ]);
    payload = dashboard;
    profileName = profile?.name?.split(" ")[0] ?? "Student";
  } catch (error) {
    return (
      <ErrorState
        message={error instanceof ApiError ? error.message : undefined}
      />
    );
  }

  const { stats, has_preferences: hasPreferences } = payload;

  return (
    <>
      <PageHeader
        eyebrow={BRAND.tagline}
        title={`${greeting()}, ${profileName}`}
        description="Here is what's worth knowing today."
        actions={
          <ButtonLink href="/opportunities" size="sm" variant="secondary">
            Browse all
          </ButtonLink>
        }
      />

      {/*
        A status line, not a claim of freshness. The catalogue is curated by
        hand and nothing re-checks it, so the indicator says exactly that.
      */}
      <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-[12px] text-muted">
        <span aria-hidden className="size-1.5 rounded-full bg-accent" />
        Curated opportunity intelligence
        <span className="text-faint">· {stats.total} opportunities tracked</span>
      </p>

      <section aria-label="Your numbers" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatsCard
          label="Newly added"
          value={stats.new_today}
          hint="Added to the catalogue"
          href="/opportunities?sort=newest"
          tone="accent"
          icon={<IconBolt />}
        />
        <StatsCard
          label="Closing soon"
          value={stats.closing_soon}
          hint={stats.closing_soon > 0 ? "Within 14 days" : "No dates published yet"}
          href="/deadlines"
          tone="critical"
          icon={<IconClock />}
        />
        <StatsCard
          label="Saved"
          value={stats.saved}
          hint="On your list"
          href="/saved"
          icon={<IconBookmark />}
        />
        <StatsCard
          label="Matched to you"
          value={stats.matched}
          hint="Scoring 60% or higher"
          href="/opportunities?sort=relevance"
          tone="verified"
          icon={<IconSparkles />}
        />
      </section>

      {!hasPreferences ? (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-panel border border-accent/30 bg-accent-soft px-4 py-3.5">
          <p className="text-[13px] text-text">
            <span className="font-semibold">Set up your profile</span> — matching uses your
            degree, skills and interests. Without it, everything is ranked by deadline alone.
          </p>
          <ButtonLink href="/profile" size="sm">
            Set preferences
          </ButtonLink>
        </div>
      ) : null}

      <Shelf
        title="Recommended for you"
        description="Ranked by how well each one fits your profile."
        icon={<IconSparkles />}
        href="/opportunities?sort=relevance"
        opportunities={payload.recommended}
        emptyTitle="Nothing to recommend yet"
        emptyBody="Add your skills and interests in your profile and this fills up straight away."
      />

      <Shelf
        title="New today"
        description="Most recently added to the catalogue."
        icon={<IconBolt />}
        href="/opportunities?sort=newest"
        opportunities={payload.new_today}
        emptyTitle="Nothing added recently"
        emptyBody="New records appear here as they are curated, and later as source checking brings them in automatically."
      />

      <Shelf
        title="Closing soon"
        description="Opportunities with a published deadline inside the next two weeks."
        icon={<IconClock />}
        href="/deadlines"
        opportunities={payload.closing_soon}
        emptyTitle="No deadlines published yet"
        emptyBody="Zenkai only shows a date where the official source publishes one. These fill in as source checking is rolled out — it never guesses at a deadline."
      />

      <Shelf
        title="Recently updated"
        description="Records whose details changed most recently."
        icon={<IconRadar />}
        href="/opportunities?sort=updated"
        opportunities={payload.recently_updated}
        emptyTitle="No recent updates"
        emptyBody="Updates appear here when a record's details or verification status change."
      />

      <p className="mt-10 border-t border-border pt-5 text-[12px] leading-relaxed text-faint">
        Today&apos;s catalogue is curated by hand from official pages, and every record carries its
        status. <span className="font-medium text-muted">Curated</span> means a person wrote the
        record from the official page — nothing re-checks it afterwards, so confirm details at the
        source before applying. Deadlines and costs appear only where the source publishes them.{" "}
        <Link href="/admin" className="text-accent hover:underline">
          See the review queue
        </Link>
        .
      </p>
    </>
  );
}
