import { Badge, Dot } from "@/components/ui/Badge";
import {
  IconAward,
  IconBriefcase,
  IconGraduationCap,
  IconSparkles,
  IconTrophy,
  IconUsers,
} from "@/components/ui/Icons";
import {
  CATEGORY_SHORT,
  COST_LABELS,
  cx,
  deadlineLabel,
  isFree,
  STATUS_EXPLANATIONS,
  STATUS_LABELS,
  urgencyOf,
} from "@/lib/format";
import type { Category, CostType, Opportunity, VerificationStatus } from "@/lib/types";

const CATEGORY_ICONS: Record<Category, typeof IconAward> = {
  certifications: IconAward,
  internships: IconBriefcase,
  hackathons: IconTrophy,
  programs: IconUsers,
  tech_benefits: IconSparkles,
  scholarships: IconGraduationCap,
};

export function CategoryBadge({ category }: { category: Category }) {
  const Glyph = CATEGORY_ICONS[category];
  return (
    <Badge tone="neutral">
      <Glyph />
      {CATEGORY_SHORT[category]}
    </Badge>
  );
}

const STATUS_TONE = {
  curated: "accent",
  source_checked: "verified",
  needs_review: "review",
  expired: "expired",
  rejected: "expired",
} as const;

const STATUS_DOT = {
  curated: "bg-accent",
  source_checked: "bg-verified",
  needs_review: "bg-review",
  expired: "bg-expired",
  rejected: "bg-expired",
} as const;

/**
 * States where the record came from and how far it has been established.
 *
 * Deliberately never says "verified", "live" or "checked N minutes ago": the
 * catalogue is curated by hand and nothing re-checks it, so any phrasing that
 * implies freshness would be a claim the system cannot support.
 */
export function SourceStatusBadge({
  status,
  className,
}: {
  status: VerificationStatus;
  className?: string;
}) {
  return (
    <Badge tone={STATUS_TONE[status]} title={STATUS_EXPLANATIONS[status]} className={className}>
      <Dot className={STATUS_DOT[status]} />
      {STATUS_LABELS[status]}
    </Badge>
  );
}

const URGENCY_TONE = {
  closed: "expired",
  today: "critical",
  critical: "critical",
  soon: "soon",
  upcoming: "calm",
  rolling: "calm",
} as const;

/**
 * Shows a countdown only where a real deadline exists. Where the official
 * source publishes none, it says so instead of implying one was found.
 */
export function DeadlineBadge({
  opportunity,
}: {
  opportunity: Pick<Opportunity, "days_left" | "is_rolling" | "deadline">;
}) {
  const unlisted = !opportunity.is_rolling && opportunity.deadline === null;
  const urgency = urgencyOf(opportunity.days_left, opportunity.is_rolling);

  return (
    <Badge
      tone={unlisted ? "neutral" : URGENCY_TONE[urgency]}
      className="tnum"
      title={
        unlisted
          ? "This programme does not publish a standing deadline. Check the official source for the current cycle."
          : opportunity.is_rolling
            ? "Applications are accepted continuously."
            : undefined
      }
    >
      {deadlineLabel(opportunity)}
    </Badge>
  );
}

export function CostBadge({ cost }: { cost: CostType }) {
  if (cost === "unknown") {
    return (
      <Badge tone="neutral" title="The official page does not publish a price.">
        Cost not confirmed
      </Badge>
    );
  }
  return <Badge tone={isFree(cost) ? "verified" : "neutral"}>{COST_LABELS[cost]}</Badge>;
}

/** A compact, high-contrast match indicator. Rule-based, never presented as AI. */
export function MatchBadge({ score, className }: { score: number; className?: string }) {
  const strong = score >= 75;
  return (
    <span
      title="Match score from your profile: category, interests, skills, location and deadline. Rule-based, not a prediction."
      className={cx(
        "tnum inline-flex items-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold",
        strong ? "bg-accent-soft text-accent" : "bg-bg-subtle text-muted",
        className,
      )}
    >
      {score}% match
    </span>
  );
}
