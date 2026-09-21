import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/layout/PageHeader";
import { CredentialPanel } from "@/components/opportunity/CredentialPanel";
import { SaveButton } from "@/components/opportunity/SaveButton";
import {
  CategoryBadge,
  CostBadge,
  DeadlineBadge,
  SourceStatusBadge,
} from "@/components/opportunity/badges";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import { ExternalLink, hostOf } from "@/components/ui/ExternalLink";
import {
  IconArrowRight,
  IconCheck,
  IconDatabase,
  IconGlobe,
  IconPin,
  IconShield,
  IconSparkles,
} from "@/components/ui/Icons";
import { api, ApiError } from "@/lib/api";
import {
  CATEGORY_LABELS,
  CATEGORY_SHORT,
  cx,
  formatDate,
  METHOD_LABELS,
  showsCost,
  STATUS_EXPLANATIONS,
  typeLabel,
} from "@/lib/format";
import type { OpportunityDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

/**
 * Deliberately does NOT call `notFound()`.
 *
 * Throwing the 404 from metadata aborts the segment tree, so Next replies with
 * a bare 404 and no UI. The page component below owns that decision, which
 * renders `not-found.tsx` *and* sets the status — but only because this segment
 * has no `loading.tsx`; see ../README.md.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  try {
    const opportunity = await api.opportunity(slug);
    return {
      title: opportunity.title,
      description: opportunity.summary,
    };
  } catch {
    return { title: "Opportunity not found" };
  }
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-border py-3 last:border-0">
      <dt className="text-[11px] font-semibold uppercase tracking-[0.07em] text-faint">{label}</dt>
      <dd className="mt-1 text-[13px] leading-relaxed text-text">{children}</dd>
    </div>
  );
}

/**
 * Information status.
 *
 * The single most important block on the page. It states plainly where the
 * record came from, how far it has been established, and that the student must
 * confirm the details themselves — rather than letting a coloured badge imply
 * more confidence than the system has.
 */
function InformationStatus({ opportunity }: { opportunity: OpportunityDetail }) {
  const originCopy: Record<string, string> = {
    seed: "Part of the curated launch catalogue.",
    ingested: "Discovered by the ingestion pipeline.",
    manual: "Entered directly by a reviewer.",
  };

  return (
    <section
      aria-labelledby="information-status"
      className="rounded-panel border border-border bg-surface p-5"
    >
      <h2
        id="information-status"
        className="flex items-center gap-2 text-[13px] font-semibold text-text"
      >
        <IconShield className="text-[15px] text-faint" />
        Information status
      </h2>

      <div className="mt-3 rounded-card border border-border bg-bg-subtle p-3.5">
        <SourceStatusBadge status={opportunity.verification_status} />
        <p className="mt-2 text-[12.5px] leading-relaxed text-muted">
          {STATUS_EXPLANATIONS[opportunity.verification_status]}
        </p>
      </div>

      <p className="mt-3 text-[12.5px] font-medium leading-relaxed text-text">
        Details may change. Verify eligibility, deadline, cost and availability on the official
        source before applying.
      </p>

      <dl className="mt-1">
        <Field label="How this was established">
          {METHOD_LABELS[opportunity.verification_method]}
          {opportunity.verified_by ? (
            <span className="mt-0.5 block text-[12px] text-faint">
              by {opportunity.verified_by}
              {opportunity.verified_at ? ` · ${formatDate(opportunity.verified_at)}` : null}
            </span>
          ) : null}
        </Field>
        <Field label="Record origin">
          {originCopy[opportunity.data_origin] ?? opportunity.data_origin}
        </Field>
        <Field label="Where the button goes">
          {opportunity.destination.is_fallback ? (
            <>
              The provider&apos;s own page.
              <span className="mt-0.5 block text-[12px] leading-relaxed text-faint">
                No exact enrolment page is on record for this one, so Zenkai sends you to the
                official source rather than guessing at a link.
              </span>
            </>
          ) : (
            <>
              Straight to where you can {opportunity.destination.label.toLowerCase()}.
              <span className="mt-0.5 block break-all text-[12px] text-faint">
                {hostOf(opportunity.destination.url)}
              </span>
            </>
          )}
        </Field>
        <Field label="Official source">
          <ExternalLink
            href={opportunity.source_url}
            className="inline-flex items-center gap-1.5 break-all text-accent hover:underline"
          >
            {hostOf(opportunity.source_url)}
          </ExternalLink>
          {opportunity.source ? (
            <span className="mt-1 block text-[12px] text-faint">
              Registered as &ldquo;{opportunity.source.name}&rdquo; · trust level{" "}
              {opportunity.source.trust_level}/5
            </span>
          ) : null}
        </Field>
        <Field label="Added to Zenkai">{formatDate(opportunity.discovered_at)}</Field>
        {opportunity.published_at ? (
          <Field label="Published by source">{formatDate(opportunity.published_at)}</Field>
        ) : null}
      </dl>

      <ExternalLink
        href={opportunity.destination.url}
        className="mt-4 inline-flex h-9 w-full items-center justify-center gap-2 rounded-[10px] border border-border-strong bg-surface text-[13px] font-medium text-text transition-colors hover:bg-bg-subtle"
      >
        {opportunity.destination.label}
      </ExternalLink>
    </section>
  );
}

function WhyRelevant({ opportunity }: { opportunity: OpportunityDetail }) {
  const match = opportunity.match;
  if (!match || match.score === 0 || match.reasons.length === 0) return null;

  return (
    <section
      aria-labelledby="relevance-heading"
      className="rounded-panel border border-accent/30 bg-accent-soft p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <h2
          id="relevance-heading"
          className="flex items-center gap-2 text-[13px] font-semibold text-text"
        >
          <IconSparkles className="text-[15px] text-accent" />
          Why this is relevant to you
        </h2>
        <span className="tnum text-[13px] font-semibold text-accent">{match.score}% match</span>
      </div>

      <ul className="mt-3 space-y-2">
        {match.reasons.map((reason) => (
          <li key={reason.label} className="flex items-start gap-2 text-[13px] leading-relaxed">
            <IconCheck className="mt-[3px] text-[13px] text-accent" />
            <span className="text-text">{reason.detail}</span>
          </li>
        ))}
      </ul>

      <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
        Scored from your profile using fixed rules — category, interests, skills, location and
        deadline. It is not a prediction of whether you will be accepted.{" "}
        <Link href="/profile" className="font-medium text-accent hover:underline">
          Update your profile
        </Link>
      </p>
    </section>
  );
}

export default async function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let opportunity: OpportunityDetail;
  try {
    opportunity = await api.opportunity(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const { destination } = opportunity;

  return (
    <div className="mx-auto max-w-6xl">
      <nav aria-label="Breadcrumb" className="mb-5 flex items-center gap-1.5 text-[12.5px] text-muted">
        <Link href="/opportunities" className="hover:text-text">
          Opportunities
        </Link>
        <span aria-hidden className="text-faint">/</span>
        <Link
          href={`/opportunities?category=${opportunity.category}`}
          className="hover:text-text"
        >
          {CATEGORY_LABELS[opportunity.category]}
        </Link>
      </nav>

      <PageHeader
        eyebrow={opportunity.organization.name}
        title={opportunity.title}
        description={opportunity.summary}
        actions={
          <>
            <SaveButton
              opportunityId={opportunity.id}
              saved={opportunity.is_saved}
              variant="full"
            />
            {/* Secondary, and only when it differs from where the button goes. */}
            {!destination.is_fallback && opportunity.source_url !== destination.url ? (
              <ExternalLink
                href={opportunity.source_url}
                className="inline-flex h-10 items-center gap-2 rounded-[10px] border border-border-strong bg-surface px-4 text-sm font-medium text-text transition-colors hover:bg-bg-subtle"
              >
                Official source
              </ExternalLink>
            ) : null}
            {/* The primary action, deliberately the strongest thing on the page. */}
            <ExternalLink
              href={destination.url}
              title={
                destination.is_fallback
                  ? "No exact enrolment page is on record, so this opens the provider's own page."
                  : undefined
              }
              className={cx(
                "inline-flex h-10 items-center gap-2 rounded-[10px] px-5 text-sm font-medium transition-colors",
                destination.is_fallback
                  ? "border border-border-strong bg-surface text-text hover:bg-bg-subtle"
                  : "bg-accent text-white shadow-card hover:bg-accent-hover",
              )}
            >
              {destination.label}
            </ExternalLink>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-1.5 pb-6">
        <CategoryBadge category={opportunity.category} />
        {/* The type only adds information when it differs from the category. */}
        {typeLabel(opportunity.opportunity_type) !== CATEGORY_SHORT[opportunity.category] ? (
          <Badge tone="neutral">{typeLabel(opportunity.opportunity_type)}</Badge>
        ) : null}
        {showsCost(opportunity) ? <CostBadge cost={opportunity.cost_type} /> : null}
        <DeadlineBadge opportunity={opportunity} />
        <Badge tone="neutral">
          {opportunity.is_remote ? <IconGlobe /> : <IconPin />}
          {opportunity.is_remote ? "Remote" : opportunity.location}
        </Badge>
        <SourceStatusBadge status={opportunity.verification_status} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <section
            aria-labelledby="about-heading"
            className="rounded-panel border border-border bg-surface p-5 sm:p-6"
          >
            <h2 id="about-heading" className="text-[13px] font-semibold text-text">
              About this opportunity
            </h2>
            <p className="mt-3 whitespace-pre-line text-[14px] leading-[1.75] text-muted">
              {opportunity.description}
            </p>
          </section>

          <div className="grid gap-6 sm:grid-cols-2">
            {opportunity.eligibility || opportunity.who_can_apply.length > 0 ? (
              <section
                aria-labelledby="eligibility-heading"
                className="rounded-panel border border-border bg-surface p-5"
              >
                <h2 id="eligibility-heading" className="text-[13px] font-semibold text-text">
                  Who can apply
                </h2>
                {opportunity.eligibility ? (
                  <p className="mt-2.5 text-[13px] leading-relaxed text-muted">
                    {opportunity.eligibility}
                  </p>
                ) : null}
                {opportunity.who_can_apply.length > 0 ? (
                  <ul className="mt-3 flex flex-wrap gap-1.5">
                    {opportunity.who_can_apply.map((item) => (
                      <li key={item}>
                        <Badge tone="neutral">{item}</Badge>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ) : null}

            {opportunity.benefits.length > 0 ? (
              <section
                aria-labelledby="benefits-heading"
                className="rounded-panel border border-border bg-surface p-5"
              >
                <h2 id="benefits-heading" className="text-[13px] font-semibold text-text">
                  What you get
                </h2>
                <ul className="mt-2.5 space-y-2">
                  {opportunity.benefits.map((benefit) => (
                    <li key={benefit} className="flex items-start gap-2 text-[13px] leading-relaxed">
                      <IconCheck className="mt-[3px] text-[13px] text-verified" />
                      <span className="text-muted">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </div>

          {opportunity.skills.length > 0 || opportunity.tags.length > 0 ? (
            <section
              aria-labelledby="topics-heading"
              className="rounded-panel border border-border bg-surface p-5"
            >
              <h2 id="topics-heading" className="text-[13px] font-semibold text-text">
                Skills and topics
              </h2>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {opportunity.skills.map((skill) => (
                  <Link key={skill} href={`/opportunities?q=${encodeURIComponent(skill)}`}>
                    <Badge tone="accent">{skill}</Badge>
                  </Link>
                ))}
                {opportunity.tags.map((tag) => (
                  <Link key={tag} href={`/opportunities?q=${encodeURIComponent(tag)}`}>
                    <Badge tone="neutral">#{tag}</Badge>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
        </div>

        <aside className="space-y-6">
          <WhyRelevant opportunity={opportunity} />

          {/* Certification-specific facts, where the category has them. */}
          {opportunity.credential ? (
            <CredentialPanel credential={opportunity.credential} />
          ) : null}

          <InformationStatus opportunity={opportunity} />

          <section
            aria-labelledby="facts-heading"
            className="rounded-panel border border-border bg-surface p-5"
          >
            <h2
              id="facts-heading"
              className="flex items-center gap-2 text-[13px] font-semibold text-text"
            >
              <IconDatabase className="text-[15px] text-faint" />
              Key facts
            </h2>
            <dl className="mt-2">
              <Field label="Organisation">
                {opportunity.organization.website ? (
                  <ExternalLink
                    href={opportunity.organization.website}
                    showIcon={false}
                    className="text-accent hover:underline"
                  >
                    {opportunity.organization.name}
                  </ExternalLink>
                ) : (
                  opportunity.organization.name
                )}
              </Field>
              <Field label="Category">{CATEGORY_LABELS[opportunity.category]}</Field>
              <Field label="Type">{typeLabel(opportunity.opportunity_type)}</Field>
              <Field label="Cost">
                <CostBadge cost={opportunity.cost_type} />
              </Field>
              <Field label="Location">
                {opportunity.is_remote ? "Remote / anywhere" : opportunity.location}
              </Field>
              <Field label="Deadline">
                {opportunity.is_rolling ? (
                  "Applications open continuously"
                ) : opportunity.deadline ? (
                  formatDate(opportunity.deadline)
                ) : (
                  <>
                    Deadline not listed
                    <span className="mt-1 block text-[11.5px] leading-relaxed text-faint">
                      This programme does not publish a standing date. Check the official source
                      for the current cycle.
                    </span>
                  </>
                )}
              </Field>
            </dl>

            <ButtonLink
              href={`/opportunities?organization=${opportunity.organization.slug}`}
              variant="secondary"
              size="sm"
              className="mt-4 w-full"
            >
              More from {opportunity.organization.name}
              <IconArrowRight className="text-[14px]" />
            </ButtonLink>
          </section>

        </aside>
      </div>
    </div>
  );
}
