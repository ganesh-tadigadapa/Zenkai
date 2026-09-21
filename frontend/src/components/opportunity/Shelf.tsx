import Link from "next/link";
import type { ReactNode } from "react";

import { OpportunityCard } from "@/components/opportunity/OpportunityCard";
import { EmptyState } from "@/components/ui/States";
import { IconArrowRight } from "@/components/ui/Icons";
import type { Opportunity } from "@/lib/types";

/**
 * A titled row of opportunity cards. The dashboard is a stack of these, which
 * is what makes it answer "what should I know right now?" rather than being a
 * generic list.
 */
export function Shelf({
  title,
  description,
  icon,
  href,
  opportunities,
  showMatch = true,
  emptyTitle,
  emptyBody,
}: {
  title: string;
  description?: string;
  icon?: ReactNode;
  href?: string;
  opportunities: Opportunity[];
  showMatch?: boolean;
  emptyTitle: string;
  emptyBody: string;
}) {
  return (
    <section className="pt-8 first:pt-0">
      <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <h2 className="flex items-center gap-2 text-[15px] font-semibold tracking-[-0.01em] text-text">
            {icon ? <span className="text-[15px] text-faint">{icon}</span> : null}
            {title}
          </h2>
          {description ? <p className="mt-0.5 text-[12.5px] text-muted">{description}</p> : null}
        </div>
        {href ? (
          <Link
            href={href}
            className="inline-flex items-center gap-1 text-[12.5px] font-medium text-accent hover:underline"
          >
            View all
            <IconArrowRight className="text-[13px]" />
          </Link>
        ) : null}
      </div>

      {opportunities.length === 0 ? (
        <EmptyState title={emptyTitle} body={emptyBody} className="py-10" />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {opportunities.slice(0, 3).map((opportunity) => (
            <OpportunityCard
              key={opportunity.id}
              opportunity={opportunity}
              showMatch={showMatch}
            />
          ))}
        </div>
      )}
    </section>
  );
}
