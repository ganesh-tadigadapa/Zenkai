import Link from "next/link";

import { SaveButton } from "@/components/opportunity/SaveButton";
import {
  CategoryBadge,
  CostBadge,
  DeadlineBadge,
  MatchBadge,
  SourceStatusBadge,
} from "@/components/opportunity/badges";
import { CredentialBadge } from "@/components/opportunity/CredentialPanel";
import { ExternalLink } from "@/components/ui/ExternalLink";
import { IconGlobe, IconPin } from "@/components/ui/Icons";
import { cx, showsCost, typeLabel } from "@/lib/format";
import type { Opportunity } from "@/lib/types";

/**
 * The product's core unit.
 *
 * Every card answers the same five questions in one pass: who is offering it,
 * what it is, what it costs, when it closes, and how far the record has been
 * established. The official source is one click away from the card itself, so a
 * student can check a claim without first opening the detail page.
 */
export function OpportunityCard({
  opportunity,
  showMatch = true,
  className,
}: {
  opportunity: Opportunity;
  showMatch?: boolean;
  className?: string;
}) {
  const match =
    showMatch && opportunity.match && opportunity.match.score > 0 ? opportunity.match : null;
  const { destination } = opportunity;

  return (
    <article
      className={cx(
        "group relative flex h-full flex-col rounded-panel border border-border bg-surface p-5",
        "transition-[border-color,box-shadow,transform] duration-200",
        "hover:-translate-y-px hover:border-border-strong hover:shadow-float",
        "focus-within:border-accent focus-within:shadow-float",
        className,
      )}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-medium text-muted">
            {opportunity.organization.name}
          </p>
          <h3 className="mt-1 text-[15px] font-semibold leading-snug text-text">
            {/* Stretched link keeps the whole card clickable without nesting anchors. */}
            <Link
              href={`/opportunities/${opportunity.slug}`}
              className="after:absolute after:inset-0 after:content-[''] hover:text-accent"
            >
              {opportunity.title}
            </Link>
          </h3>
        </div>

        {/* Raised above the stretched link so the controls stay clickable. */}
        <div className="relative z-10 flex shrink-0 items-center gap-2">
          {match ? <MatchBadge score={match.score} /> : null}
          <SaveButton opportunityId={opportunity.id} saved={opportunity.is_saved} />
        </div>
      </header>

      <p className="mt-2.5 line-clamp-2 text-[13px] leading-relaxed text-muted">
        {opportunity.summary}
      </p>

      <div className="mt-3.5 flex flex-wrap items-center gap-1.5">
        {/* The credential badge is more specific than the category, so it
            replaces it where the record establishes what is earned. */}
        {opportunity.credential && opportunity.credential.credential_type !== "unknown" ? (
          <CredentialBadge credential={opportunity.credential} />
        ) : (
          <CategoryBadge category={opportunity.category} />
        )}
        {showsCost(opportunity) ? <CostBadge cost={opportunity.cost_type} /> : null}
        <DeadlineBadge opportunity={opportunity} />
      </div>

      <div className="mt-3.5 flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-border pt-3.5">
        <SourceStatusBadge status={opportunity.verification_status} />
        <span className="inline-flex min-w-0 items-center gap-1.5 text-[12px] text-faint">
          {opportunity.is_remote ? <IconGlobe /> : <IconPin />}
          <span className="truncate">
            {opportunity.is_remote ? "Remote" : opportunity.location}
          </span>
        </span>
      </div>

      {/*
        The primary action goes straight to where the student can act, so
        nobody has to search a provider's site from the feed. `relative z-10`
        lifts these above the title's stretched overlay so clicks land here.
      */}
      <footer className="relative z-10 mt-auto flex items-center gap-2 pt-3.5">
        <ExternalLink
          href={destination.url}
          title={
            destination.is_fallback
              ? "No exact enrolment page is on record, so this opens the provider's own page."
              : undefined
          }
          className={cx(
            "inline-flex h-9 flex-1 items-center justify-center gap-1.5 rounded-[10px]",
            "text-[13px] font-medium transition-colors",
            destination.is_fallback
              ? "border border-border-strong bg-surface text-text hover:bg-bg-subtle"
              : "bg-accent text-white hover:bg-accent-hover",
          )}
        >
          {destination.label}
        </ExternalLink>

        {/* Only worth showing when it is somewhere different from the button. */}
        {!destination.is_fallback && opportunity.source_url !== destination.url ? (
          <ExternalLink
            href={opportunity.source_url}
            ariaLabel={`Official source for ${opportunity.title}`}
            className="inline-flex h-9 shrink-0 items-center gap-1 rounded-[10px] border border-border px-3 text-[12.5px] font-medium text-muted transition-colors hover:bg-bg-subtle hover:text-text"
          >
            Source
          </ExternalLink>
        ) : null}
      </footer>
    </article>
  );
}

/** Compact row used in dense lists (deadlines, saved). */
export function OpportunityRow({ opportunity }: { opportunity: Opportunity }) {
  return (
    <article className="group relative flex flex-wrap items-center gap-x-4 gap-y-2 rounded-card border border-border bg-surface px-4 py-3 transition-colors hover:border-border-strong hover:bg-bg-subtle sm:flex-nowrap">
      <div className="min-w-0 flex-1 basis-full sm:basis-auto">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <h3 className="truncate text-sm font-semibold text-text">
            <Link
              href={`/opportunities/${opportunity.slug}`}
              className="after:absolute after:inset-0 after:content-[''] hover:text-accent"
            >
              {opportunity.title}
            </Link>
          </h3>
          {opportunity.match && opportunity.match.score > 0 ? (
            <MatchBadge score={opportunity.match.score} />
          ) : null}
        </div>
        <p className="mt-0.5 truncate text-[12px] text-muted">
          {opportunity.organization.name} · {typeLabel(opportunity.opportunity_type)} ·{" "}
          {opportunity.is_remote ? "Remote" : opportunity.location}
        </p>
      </div>

      <div className="relative z-10 flex shrink-0 items-center gap-2">
        {/* The countdown is the point of this row — keep it at every width. */}
        <DeadlineBadge opportunity={opportunity} />
        <SaveButton opportunityId={opportunity.id} saved={opportunity.is_saved} />
      </div>
    </article>
  );
}
