import type { Metadata } from "next";
import { Suspense } from "react";

import { ActiveFilters } from "@/components/filters/ActiveFilters";
import { FilterPanel } from "@/components/filters/FilterPanel";
import { Pagination } from "@/components/filters/Pagination";
import { SortSelect } from "@/components/filters/SortSelect";
import { PageHeader } from "@/components/layout/PageHeader";
import { OpportunityGrid } from "@/components/opportunity/OpportunityGrid";
import { GlobalSearch } from "@/components/search/GlobalSearch";
import { ErrorState, GridSkeleton } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/format";
import type { Category } from "@/lib/types";

export const metadata: Metadata = { title: "Opportunities" };
export const dynamic = "force-dynamic";

const PAGE_SIZE = 24;

type SearchParams = Record<string, string | string[] | undefined>;

function asArray(value: string | string[] | undefined): string[] {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

/*
  Every narrowing param the filter rail can set must be forwarded here. A param
  present in the URL and rendered as a chip but missing from this object is a
  control that silently does nothing — which is worse than no control at all,
  because the chip says it is working.

  NARROWING_PARAMS below is the shared list; keep the two in step.
*/
function buildQuery(params: SearchParams, offset: number) {
  return {
    q: typeof params.q === "string" ? params.q : undefined,
    category: asArray(params.category),
    type: asArray(params.type),
    cost: asArray(params.cost),
    organization: asArray(params.organization),
    skill: asArray(params.skill),
    credential_type: asArray(params.credential_type),
    specialization: asArray(params.specialization),
    assessment: asArray(params.assessment),
    proctored: asArray(params.proctored),
    delivery: asArray(params.delivery),
    level: asArray(params.level),
    issuer: asArray(params.issuer),
    free_only: params.free_only === "true" ? "true" : undefined,
    verified_only: params.verified_only === "true" ? "true" : undefined,
    remote: params.remote === "true" ? "true" : undefined,
    deadline_within_days:
      typeof params.deadline_within_days === "string" ? params.deadline_within_days : undefined,
    sort: typeof params.sort === "string" ? params.sort : "deadline",
    limit: PAGE_SIZE,
    offset,
  };
}

function headingFor(params: SearchParams): { title: string; description: string } {
  const categories = asArray(params.category);
  if (categories.length === 1) {
    const category = categories[0] as Category;
    const label = CATEGORY_LABELS[category];
    if (label) {
      return {
        title: label,
        description: `Every ${label.toLowerCase()} record in the catalogue, newest checks first.`,
      };
    }
  }
  if (typeof params.q === "string" && params.q) {
    return {
      title: `Results for “${params.q}”`,
      description: "Searched across titles, organisations, descriptions, skills and tags.",
    };
  }
  return {
    title: "All opportunities",
    description:
      "Filter by category, cost, deadline and verification status. Every filter is in the URL, so you can share the view.",
  };
}

/** Params that narrow results, as opposed to sorting or paging them. */
const NARROWING_PARAMS = [
  "q", "category", "type", "cost", "organization", "skill", "free_only",
  "verified_only", "remote", "deadline_within_days", "credential_type",
  "specialization", "assessment", "proctored", "delivery", "level", "issuer",
] as const;

function activeFilterCount(params: SearchParams): number {
  return NARROWING_PARAMS.reduce((total, key) => total + asArray(params[key]).length, 0);
}

async function Results({ params }: { params: SearchParams }) {
  const offset = Number(params.offset ?? 0) || 0;

  let page;
  try {
    page = await api.opportunities(buildQuery(params, offset));
  } catch (error) {
    return <ErrorState message={error instanceof ApiError ? error.message : undefined} />;
  }

  /*
    When filters hide everything, saying "nothing matches" is unhelpful if the
    category is actually full. Fetch the unfiltered count for the same category
    so the empty state can name what is being excluded and offer a way back.
  */
  let categoryTotal: number | null = null;
  const categories = asArray(params.category);
  if (page.total === 0 && activeFilterCount(params) > categories.length) {
    categoryTotal = await api
      .opportunities({ category: categories, limit: 1 })
      .then((result) => result.total)
      .catch(() => null);
  }

  function buildHref(nextOffset: number) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (key === "offset" || value === undefined) continue;
      asArray(value).forEach((item) => search.append(key, item));
    }
    if (nextOffset > 0) search.set("offset", String(nextOffset));
    return `/opportunities?${search.toString()}`;
  }

  return (
    <>
      <p className="tnum mb-4 text-[12.5px] text-muted">
        <span className="font-medium text-text">{page.total}</span>{" "}
        {page.total === 1 ? "opportunity" : "opportunities"}
      </p>

      <OpportunityGrid
        opportunities={page.items}
        emptyTitle={
          categoryTotal
            ? `Your filters exclude all ${categoryTotal} of them`
            : "Nothing matches those filters"
        }
        emptyBody={
          categoryTotal
            ? "Most of the catalogue has facts the provider never published — cost and proctoring especially — and filters on those exclude anything unstated. Clear a filter above to see the rest."
            : "Try removing a filter, widening the deadline window, or searching for a broader term."
        }
      />

      <Pagination
        total={page.total}
        limit={page.limit}
        offset={page.offset}
        buildHref={buildHref}
      />
    </>
  );
}

export default async function OpportunitiesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const facets = await api.facets().catch(() => ({}));
  const { title, description } = headingFor(params);

  // Changing any param remounts Results, so Suspense shows the skeleton again.
  const suspenseKey = JSON.stringify(params);

  return (
    <>
      <PageHeader title={title} description={description} />

      {/* Only a flex row once the filter rail exists. Below lg the rail is
          hidden and the trigger button must not become a flex sibling of the
          results column, which would push the grid off-screen. */}
      <div className="lg:flex lg:gap-8">
        <FilterPanel facets={facets} />

        <div className="min-w-0 flex-1">
          <div className="mb-4 flex flex-wrap items-center gap-2.5">
            <div className="min-w-[200px] flex-1 md:hidden">
              <GlobalSearch />
            </div>
            <div className="ml-auto flex items-center gap-2.5">
              <SortSelect />
            </div>
          </div>

          <div className="mb-5">
            <ActiveFilters />
          </div>

          <Suspense key={suspenseKey} fallback={<GridSkeleton count={9} />}>
            <Results params={params} />
          </Suspense>
        </div>
      </div>
    </>
  );
}
