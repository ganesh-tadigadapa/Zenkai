/** Mirrors the Pydantic schemas in backend/app/schemas. */

export type Category =
  | "certifications"
  | "internships"
  | "hackathons"
  | "programs"
  | "tech_benefits"
  | "scholarships";

export type CostType =
  | "free"
  | "free_for_students"
  | "discounted"
  | "paid"
  | "freemium"
  | "subscription"
  | "exam_fee"
  | "unknown";

/**
 * How much confidence the product may express about a record.
 * `source_checked` is reserved for records an automated check actually fetched;
 * nothing writes it until source checking exists.
 */
export type VerificationStatus =
  | "curated"
  | "source_checked"
  | "needs_review"
  | "expired"
  | "rejected";

/** How the current verification status was arrived at. */
export type VerificationMethod =
  | "none"
  | "curation"
  | "human_review"
  | "source_fetch"
  | "automated";

export type DataOrigin = "seed" | "ingested" | "manual";

/** Which of a record's two URLs the primary CTA points at. */
export type DestinationType = "direct_destination" | "official_source";

export type DestinationAction =
  | "start_course"
  | "enroll"
  | "start_learning"
  | "register_exam"
  | "view_certification"
  | "get_access"
  | "apply"
  | "register"
  | "visit_source";

export type CredentialType =
  | "professional_certification"
  | "certification_exam"
  | "professional_certificate"
  | "university_certificate"
  | "course_certificate"
  | "completion_certificate"
  | "skill_badge"
  | "digital_credential"
  | "micro_credential"
  | "learning_program"
  | "training"
  | "exam_prep"
  | "assessment"
  | "unknown";

export type AssessmentType =
  | "proctored_exam"
  | "non_proctored_exam"
  | "project"
  | "quiz"
  | "assignment"
  | "course_completion"
  | "practical_exam"
  | "performance_based"
  | "none"
  | "unknown";

/** `unknown` means the source did not say — never that the answer is "no". */
export type ProctoredStatus = "yes" | "no" | "optional" | "unknown";

export type DeliveryMode =
  | "online"
  | "in_person"
  | "hybrid"
  | "self_paced"
  | "test_centre"
  | "unknown";

export type ExperienceLevel = "beginner" | "intermediate" | "advanced" | "unknown";

/** Certification-specific facts. Absent fields come back as `unknown`. */
export interface Credential {
  credential_type: CredentialType;
  specializations: string[];
  issuer: string | null;
  exam_code: string | null;
  assessment_type: AssessmentType;
  proctored_status: ProctoredStatus;
  delivery_mode: DeliveryMode;
  experience_level: ExperienceLevel;
  duration_hours: number | null;
  validity_months: number | null;
  available_countries: string[];
}

export type UrlCheckStatus = "ok" | "blocked" | "unreachable" | "broken" | "unchecked";

/**
 * The resolved primary call to action, decided by the API.
 *
 * `is_fallback` is true when no exact enrol/apply page could be established and
 * the button points at the provider's own page instead.
 */
export interface Destination {
  url: string;
  type: DestinationType;
  action: DestinationAction;
  label: string;
  is_fallback: boolean;
}

export type RemotePreference = "remote" | "onsite" | "any";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  website: string | null;
  logo_url: string | null;
  description: string | null;
}

export interface Source {
  id: string;
  name: string;
  url: string;
  source_type: string;
  trust_level: number;
  last_checked_at: string | null;
}

export interface MatchReason {
  label: string;
  detail: string;
  points: number;
}

export interface Match {
  score: number;
  reasons: MatchReason[];
}

export interface Opportunity {
  id: string;
  slug: string;
  title: string;
  summary: string;
  category: Category;
  opportunity_type: string;
  organization: Organization;
  location: string;
  is_remote: boolean;
  cost_type: CostType;
  cost_amount: number | null;
  currency: string | null;
  deadline: string | null;
  is_rolling: boolean;
  deadline_is_estimated: boolean;
  days_left: number | null;
  destination: Destination;
  application_url: string;
  source_url: string;
  direct_destination_url: string | null;
  skills: string[];
  tags: string[];
  verification_status: VerificationStatus;
  verification_method: VerificationMethod;
  data_origin: DataOrigin;
  last_checked_at: string | null;
  discovered_at: string;
  published_at: string | null;
  updated_at: string;
  is_saved: boolean;
  match: Match | null;
  /** Present for certifications; null for the other categories so far. */
  credential: Credential | null;
}

export interface OpportunityDetail extends Opportunity {
  description: string;
  eligibility: string | null;
  who_can_apply: string[];
  benefits: string[];
  secondary_categories: Category[];
  source: Source | null;
  url_check_status: UrlCheckStatus;
  last_url_checked_at: string | null;
  confidence: number;
  verified_at: string | null;
  verified_by: string | null;
}

export interface AdminOpportunity extends OpportunityDetail {
  content_hash: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Stats {
  total: number;
  new_today: number;
  closing_soon: number;
  saved: number;
  matched: number;
}

export interface DashboardPayload {
  stats: Stats;
  recommended: Opportunity[];
  new_today: Opportunity[];
  closing_soon: Opportunity[];
  recently_updated: Opportunity[];
  has_preferences: boolean;
}

export interface CategoryInfo {
  slug: Category;
  name: string;
  description: string;
  icon: string;
  count: number;
}

export interface FacetValue {
  value: string;
  label: string;
  count: number;
}

export type Facets = Record<string, FacetValue[]>;

export interface Preferences {
  degree: string | null;
  field_of_study: string | null;
  year: string | null;
  country: string | null;
  location: string | null;
  remote_preference: RemotePreference;
  skills: string[];
  interests: string[];
  preferred_categories: Category[];
}

export interface Profile {
  id: string;
  email: string;
  name: string;
  is_admin: boolean;
  /** True for the seeded demo account, so the UI can label it as such. */
  is_demo: boolean;
  preferences: Preferences | null;
}

export interface SavedPayload {
  active: Opportunity[];
  expired: Opportunity[];
  total: number;
}

export interface DeadlinesPayload {
  today: Opportunity[];
  this_week: Opportunity[];
  upcoming: Opportunity[];
  total: number;
}

export interface AdminStats {
  pending: number;
  verified: number;
  rejected: number;
  expired: number;
}

export interface Review {
  id: string;
  opportunity_id: string;
  reviewer: string;
  action: "approve" | "reject" | "edit";
  previous_status: VerificationStatus | null;
  new_status: VerificationStatus | null;
  notes: string | null;
  created_at: string;
}

export type SourceAuthority =
  | "official_issuer"
  | "official_organization"
  | "government"
  | "university"
  | "professional_body"
  | "established_platform"
  | "other_reputable_source"
  | "unknown";

export type DiscoveryMethod =
  | "official_api"
  | "rss"
  | "atom"
  | "sitemap"
  | "structured_data"
  | "public_webpage"
  | "manual"
  | "unknown";

export interface SourceRecord {
  id: string;
  name: string;
  organization: string | null;
  url: string;
  official_url: string | null;
  source_type: string;
  category: string | null;
  /** How much the source's word is worth — separate from whether it may be read. */
  authority: SourceAuthority;
  discovery_method: DiscoveryMethod;
  trust_level: number;
  priority: number;
  check_frequency: "high" | "normal" | "low";
  check_frequency_minutes: number;
  robots_allowed: boolean;
  access_notes: string | null;
  active: boolean;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  consecutive_failures: number;
  /** Whether this source can support a SOURCE_CHECKED record. */
  is_authoritative: boolean;
  /** "Not monitored yet." when nothing has ever read it. */
  monitoring_summary: string;
}
