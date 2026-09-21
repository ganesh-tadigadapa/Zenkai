import type {
  Category,
  CostType,
  Opportunity,
  VerificationMethod,
  VerificationStatus,
} from "./types";

export const CATEGORY_LABELS: Record<Category, string> = {
  certifications: "Certifications",
  internships: "Internships",
  hackathons: "Hackathons",
  programs: "Programs",
  tech_benefits: "Tech Benefits",
  scholarships: "Scholarships",
};

export const CATEGORY_SHORT: Record<Category, string> = {
  certifications: "Certification",
  internships: "Internship",
  hackathons: "Hackathon",
  programs: "Program",
  tech_benefits: "Tech Benefit",
  scholarships: "Scholarship",
};

export const COST_LABELS: Record<CostType, string> = {
  free: "Free",
  free_for_students: "Free for students",
  discounted: "Student discount",
  paid: "Paid",
  freemium: "Free tier, paid upgrade",
  subscription: "Subscription",
  // Free to learn, paid to sit — the distinction students most need.
  exam_fee: "Free to learn, paid exam",
  unknown: "Cost not confirmed",
};

/**
 * Deliberately modest wording. Nothing here implies a live or recent check —
 * the product only claims what it actually did.
 */
export const STATUS_LABELS: Record<VerificationStatus, string> = {
  curated: "Curated",
  source_checked: "Source checked",
  needs_review: "Needs verification",
  expired: "Closed",
  rejected: "Rejected",
};

export const STATUS_EXPLANATIONS: Record<VerificationStatus, string> = {
  curated:
    "Written by hand from the organisation's official page. Nothing re-checks it afterwards, so confirm the details at the source before applying.",
  source_checked:
    "The official source was fetched and confirmed. Details can still change — confirm at the source before applying.",
  needs_review:
    "Not yet confirmed by a reviewer. Treat every detail as unverified and check the official source.",
  expired: "Closed, or its deadline has passed.",
  rejected: "A reviewer rejected this record.",
};

/** Human-readable origin, used on the detail page's information-status panel. */
export const METHOD_LABELS: Record<VerificationMethod, string> = {
  none: "Not yet established",
  curation: "Curated by hand from the official page",
  human_review: "Confirmed by a reviewer against the official source",
  source_fetch: "Fetched automatically from the official source",
  automated: "Inferred by the extraction pipeline",
};

export const TYPE_LABELS: Record<string, string> = {
  certification: "Certification",
  exam: "Exam",
  credential: "Credential",
  course: "Course",
  learning_platform: "Learning platform",
  training: "Training",
  voucher: "Voucher",
  internship: "Internship",
  hackathon: "Hackathon",
  competition: "Competition",
  fellowship: "Fellowship",
  program: "Program",
  student_benefit: "Student benefit",
  software: "Software",
  cloud_credits: "Cloud credits",
  ai_tool: "AI tool",
  developer_tool: "Developer tool",
  scholarship: "Scholarship",
  grant: "Grant",
};

export function typeLabel(value: string): string {
  return TYPE_LABELS[value] ?? titleCase(value);
}

export function titleCase(value: string): string {
  return value
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** "2 hours ago", "3 days ago" — used for freshness indicators. */
export function relativeTime(iso: string | null): string {
  if (!iso) return "never";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "unknown";

  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return "just now";

  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["minute", 60],
    ["hour", 3600],
    ["day", 86400],
    ["week", 604800],
    ["month", 2629800],
    ["year", 31557600],
  ];

  let unit: Intl.RelativeTimeFormatUnit = "minute";
  let divisor = 60;
  for (const [candidate, size] of units) {
    if (seconds >= size) {
      unit = candidate;
      divisor = size;
    }
  }
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  return formatter.format(-Math.round(seconds / divisor), unit);
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export type Urgency = "closed" | "today" | "critical" | "soon" | "upcoming" | "rolling";

export function urgencyOf(daysLeft: number | null, isRolling = false): Urgency {
  if (isRolling || daysLeft === null) return "rolling";
  if (daysLeft < 0) return "closed";
  if (daysLeft === 0) return "today";
  if (daysLeft <= 3) return "critical";
  if (daysLeft <= 7) return "soon";
  return "upcoming";
}

/**
 * Never invents a date. An opportunity with no published deadline reads
 * "Deadline not listed", which is the truth, rather than "No deadline", which
 * would imply the organisation has confirmed there isn't one.
 */
export function deadlineLabel(
  opportunity: Pick<Opportunity, "days_left" | "is_rolling" | "deadline">,
): string {
  const { days_left: days, is_rolling: rolling, deadline } = opportunity;
  if (rolling) return "Rolling";
  if (deadline === null || days === null) return "Deadline not listed";
  if (days < 0) return "Closed";
  if (days === 0) return "Closes today";
  if (days === 1) return "1 day left";
  return `${days} days left`;
}

export function costLabel(opportunity: Pick<Opportunity, "cost_type" | "cost_amount" | "currency">) {
  if (opportunity.cost_type === "paid" && opportunity.cost_amount) {
    return `${opportunity.currency ?? ""}${opportunity.cost_amount}`.trim();
  }
  return COST_LABELS[opportunity.cost_type];
}

/**
 * Whether a cost badge tells the student anything.
 *
 * "Free" on a scholarship or an internship is noise — nobody expects to pay to
 * apply. Cost only carries information where the student might actually be
 * charged, so the badge is suppressed elsewhere unless there is a real price.
 */
const COST_RELEVANT_CATEGORIES: ReadonlySet<Category> = new Set([
  "certifications",
  "tech_benefits",
]);

/** Cost types that always carry information, whatever the category. */
const ALWAYS_INFORMATIVE: ReadonlySet<CostType> = new Set([
  "paid",
  "discounted",
  "freemium",
  "subscription",
  "exam_fee",
  "unknown",
]);

export function showsCost(opportunity: Pick<Opportunity, "category" | "cost_type">): boolean {
  if (ALWAYS_INFORMATIVE.has(opportunity.cost_type)) return true;
  return COST_RELEVANT_CATEGORIES.has(opportunity.category);
}

/**
 * Whether the student can get the whole thing at no cost.
 *
 * Deliberately excludes `exam_fee` and `freemium`: free learning behind a paid
 * exam is not a free credential, and treating it as one is exactly the
 * overclaim the cost taxonomy exists to prevent.
 */
export function isFree(cost: CostType): boolean {
  return cost === "free" || cost === "free_for_students";
}

/** Tailwind class merge helper — keeps conditional class lists readable. */
export function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}


/* --- Credential vocabulary ------------------------------------------------
   Wording chosen so "unknown" reads as "we did not establish this", never as a
   negative answer. "Not stated" is shown rather than hidden, so a student can
   see the difference between a fact and a gap.
   ------------------------------------------------------------------------- */

export const CREDENTIAL_TYPE_LABELS: Record<string, string> = {
  professional_certification: "Professional certification",
  certification_exam: "Certification exam",
  professional_certificate: "Professional certificate",
  university_certificate: "University certificate",
  course_certificate: "Course certificate",
  completion_certificate: "Completion certificate",
  skill_badge: "Skill badge",
  digital_credential: "Digital credential",
  micro_credential: "Micro-credential",
  learning_program: "Learning programme",
  training: "Training",
  exam_prep: "Exam preparation",
  assessment: "Assessment",
  unknown: "Not stated",
};

export const ASSESSMENT_LABELS: Record<string, string> = {
  proctored_exam: "Proctored exam",
  non_proctored_exam: "Unproctored exam",
  project: "Project",
  quiz: "Quiz",
  assignment: "Assignment",
  course_completion: "Course completion",
  practical_exam: "Practical exam",
  performance_based: "Performance based",
  none: "No assessment",
  unknown: "Not stated",
};

export const PROCTORED_LABELS: Record<string, string> = {
  yes: "Proctored",
  no: "Not proctored",
  optional: "Proctoring optional",
  unknown: "Proctoring not stated",
};

export const DELIVERY_LABELS: Record<string, string> = {
  online: "Online",
  in_person: "In person",
  hybrid: "Hybrid",
  self_paced: "Self-paced",
  test_centre: "Test centre",
  unknown: "Not stated",
};

export const LEVEL_LABELS: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
  unknown: "Not stated",
};

/** Specializations are a flat, extensible list, so labels are derived. */
const SPECIALIZATION_OVERRIDES: Record<string, string> = {
  aws: "AWS",
  azure: "Azure",
  google_cloud: "Google Cloud",
  devops: "DevOps",
  ai: "AI",
  llm: "LLM",
  mlops: "MLOps",
  sql: "SQL",
  iot: "IoT",
  ui_ux: "UI/UX",
  c_cpp: "C/C++",
  git_github: "Git/GitHub",
  sap: "SAP",
  generative_ai: "Generative AI",
  data_science: "Data science",
  data_analytics: "Data analytics",
  data_engineering: "Data engineering",
  machine_learning: "Machine learning",
  web_development: "Web development",
  digital_marketing: "Digital marketing",
  design_cad: "Design/CAD",
  system_design: "System design",
  servicenow: "ServiceNow",
};

export function specializationLabel(value: string): string {
  return SPECIALIZATION_OVERRIDES[value] ?? titleCase(value);
}

/** True when the credential has at least one established fact worth showing. */
export function hasStatedCredentialFacts(credential: {
  credential_type: string;
  specializations: string[];
  exam_code: string | null;
  issuer: string | null;
}): boolean {
  return (
    credential.credential_type !== "unknown" ||
    credential.specializations.length > 0 ||
    Boolean(credential.exam_code) ||
    Boolean(credential.issuer)
  );
}


export const AUTHORITY_LABELS: Record<string, string> = {
  official_issuer: "Official issuer",
  official_organization: "Official organisation",
  government: "Government",
  university: "University",
  professional_body: "Professional body",
  established_platform: "Established platform",
  other_reputable_source: "Other reputable source",
  unknown: "Not established",
};

export const DISCOVERY_LABELS: Record<string, string> = {
  official_api: "Official API",
  rss: "RSS",
  atom: "Atom",
  sitemap: "Sitemap",
  structured_data: "Structured data",
  public_webpage: "Public page",
  manual: "Manual",
  unknown: "Not established",
};
