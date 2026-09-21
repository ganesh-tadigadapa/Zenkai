import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ReviewCard } from "@/components/admin/ReviewCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { IconDatabase, IconShield } from "@/components/ui/Icons";
import { StatsCard } from "@/components/ui/StatsCard";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import { requireUser } from "@/lib/require-user";
import { AUTHORITY_LABELS, cx, DISCOVERY_LABELS, relativeTime } from "@/lib/format";
import type { VerificationStatus } from "@/lib/types";

export const metadata: Metadata = { title: "Review queue" };
export const dynamic = "force-dynamic";

const TABS: { status: VerificationStatus; label: string }[] = [
  { status: "needs_review", label: "Needs verification" },
  { status: "curated", label: "Curated" },
  { status: "source_checked", label: "Source checked" },
  { status: "rejected", label: "Rejected" },
  { status: "expired", label: "Closed" },
];

const REVIEWER = "reviewer@zenkai.dev";

export default async function AdminPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  // Hiding the nav link is presentation, not authorisation. A signed-out
  // visitor is asked to sign in; a signed-in student who types the URL gets the
  // same answer as any unknown route: this does not exist.
  const profile = await requireUser("/admin");
  if (!profile.is_admin) notFound();

  const params = await searchParams;
  const active = (TABS.find((tab) => tab.status === params.status)?.status ??
    "needs_review") as VerificationStatus;

  let stats;
  let queue;
  let sources;
  try {
    [stats, queue, sources] = await Promise.all([
      api.admin.stats(),
      api.admin.queue(active, 25),
      api.admin.sources().catch(() => []),
    ]);
  } catch (error) {
    const message = error instanceof ApiError ? error.message : undefined;
    return (
      <ErrorState
        title="Could not load the review queue"
        message={message}
        hint="Admin routes require a valid ZENKAI_ADMIN_TOKEN that matches the backend's ADMIN_TOKEN."
      />
    );
  }

  // `stats.verified` counts curated and source-checked together; the per-tab
  // totals come from the queue itself, so only the pending count is exact here.
  const counts: Partial<Record<VerificationStatus, number>> = {
    needs_review: stats.pending,
    rejected: stats.rejected,
    expired: stats.expired,
  };

  return (
    <>
      <PageHeader
        eyebrow="Operations"
        title="Review queue"
        description="Automation proposes; a reviewer decides. Approving a record marks it source checked, which is the only status that asserts someone opened the official page."
      />

      <section aria-label="Queue summary" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatsCard
          label="Needs verification"
          value={stats.pending}
          tone="critical"
          icon={<IconShield />}
        />
        <StatsCard label="Curated or checked" value={stats.verified} tone="verified" />
        <StatsCard label="Rejected" value={stats.rejected} />
        <StatsCard label="Closed" value={stats.expired} />
      </section>

      <nav
        aria-label="Queue filter"
        className="mt-8 flex flex-wrap gap-1 border-b border-border pb-px"
      >
        {TABS.map((tab) => {
          const isActive = tab.status === active;
          return (
            <Link
              key={tab.status}
              href={`/admin?status=${tab.status}`}
              aria-current={isActive ? "page" : undefined}
              className={cx(
                "inline-flex items-center gap-2 rounded-t-lg border-b-2 px-3.5 py-2 text-[13px] font-medium transition-colors",
                isActive
                  ? "border-accent text-text"
                  : "border-transparent text-muted hover:text-text",
              )}
            >
              {tab.label}
              {counts[tab.status] !== undefined ? (
                <span
                  className={cx(
                    "tnum rounded px-1.5 py-0.5 text-[11px] font-semibold",
                    isActive ? "bg-accent-soft text-accent" : "bg-bg-subtle text-faint",
                  )}
                >
                  {counts[tab.status]}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <section aria-labelledby="queue-heading" className="mt-6 space-y-4">
        {/* Names the list for screen readers and keeps the heading order
            unbroken between the page h1 and each card's h3. */}
        <h2 id="queue-heading" className="sr-only">
          {TABS.find((tab) => tab.status === active)?.label} records
        </h2>
        {queue.items.length === 0 ? (
          <EmptyState
            icon={<IconShield />}
            title={
              active === "needs_review"
                ? "Queue is clear"
                : `No ${(TABS.find((t) => t.status === active)?.label ?? active).toLowerCase()} records`
            }
            body={
              active === "needs_review"
                ? "Every record has been reviewed. New candidates appear here as the ingestion pipeline discovers them."
                : "Nothing currently sits in this state."
            }
          />
        ) : (
          queue.items.map((opportunity) => (
            <ReviewCard key={opportunity.id} opportunity={opportunity} reviewer={REVIEWER} />
          ))
        )}
      </section>

      {sources.length > 0 ? (
        <section className="mt-12 border-t border-border pt-8">
          <h2 className="flex items-center gap-2 text-[15px] font-semibold text-text">
            <IconDatabase className="text-[15px] text-faint" />
            Monitored sources
          </h2>
          <p className="mt-1 max-w-3xl text-[12.5px] leading-relaxed text-muted">
            Two independent properties. <span className="font-medium text-text">Access</span>{" "}
            decides whether a source may be read — one marked{" "}
            <span className="font-medium text-expired">blocked</span> never is, and is listed so the
            system holds an explicit record of what it must not touch.{" "}
            <span className="font-medium text-text">Authority</span> decides whether its word can
            support a source-checked record; a platform listing is useful for discovering that
            something exists but is not evidence of what it costs.
          </p>

          <div className="mt-4 overflow-x-auto rounded-panel border border-border">
            <table className="w-full min-w-[720px] border-collapse text-left">
              <thead>
                <tr className="border-b border-border bg-bg-subtle">
                  {["Source", "Authority", "Discovery", "Every", "Monitoring", "Access"].map((heading) => (
                    <th
                      key={heading}
                      scope="col"
                      className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.07em] text-faint"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3">
                      <p className="text-[13px] font-medium text-text">{source.name}</p>
                      <p className="mt-0.5 max-w-[320px] truncate text-[11.5px] text-faint">
                        {source.url}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-[12.5px] text-text">
                        {AUTHORITY_LABELS[source.authority] ?? source.authority}
                      </p>
                      <p className="mt-0.5 text-[11px] text-faint">
                        {source.is_authoritative
                          ? "Can support source-checked"
                          : "Discovery signal only"}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-[12.5px] text-muted">
                      {DISCOVERY_LABELS[source.discovery_method] ?? source.discovery_method}
                    </td>
                    <td className="tnum px-4 py-3 text-[12.5px] text-muted">
                      {source.check_frequency_minutes >= 1440
                        ? `${Math.round(source.check_frequency_minutes / 1440)}d`
                        : `${Math.round(source.check_frequency_minutes / 60)}h`}
                    </td>
                    <td className="px-4 py-3">
                      {/* Never a fabricated timestamp: a source nothing has read
                          says so in words. */}
                      <p className="text-[12.5px] text-muted">{source.monitoring_summary}</p>
                      {source.last_success_at ? (
                        <p className="mt-0.5 text-[11px] text-faint">
                          Last read {relativeTime(source.last_success_at)}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        title={source.access_notes ?? undefined}
                        className={cx(
                          "rounded-md px-2 py-0.5 text-[11px] font-medium",
                          source.robots_allowed
                            ? "bg-verified-soft text-verified"
                            : "bg-expired-soft text-expired",
                        )}
                      >
                        {source.robots_allowed ? "Permitted" : "Blocked"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </>
  );
}
