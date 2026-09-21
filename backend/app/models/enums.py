"""Domain vocabularies shared by the database models and the API schemas."""
from __future__ import annotations

from enum import Enum


class Category(str, Enum):
    """The six product categories. Deliberately closed — see ARCHITECTURE.md."""

    CERTIFICATIONS = "certifications"
    INTERNSHIPS = "internships"
    HACKATHONS = "hackathons"
    PROGRAMS = "programs"
    TECH_BENEFITS = "tech_benefits"
    SCHOLARSHIPS = "scholarships"


class OpportunityType(str, Enum):
    """What the opportunity actually *is*.

    Kept deliberately precise: a learning platform is not a certification, and a
    course that issues a completion certificate is not a credentialing exam.
    Calling them all "certification" would misrepresent what a student gets.
    """

    # Learning and credentials
    CERTIFICATION = "certification"      # a credential awarded on passing
    EXAM = "exam"                        # a paid credentialing exam
    CREDENTIAL = "credential"            # a digital badge or micro-credential
    COURSE = "course"                    # a single course, may issue a certificate
    LEARNING_PLATFORM = "learning_platform"  # a catalogue of courses, not one credential
    TRAINING = "training"                # structured training, often vendor-run
    VOUCHER = "voucher"                  # a discount or fee waiver for an exam

    # Work and experience
    INTERNSHIP = "internship"
    HACKATHON = "hackathon"
    COMPETITION = "competition"
    FELLOWSHIP = "fellowship"
    PROGRAM = "program"

    # Benefits
    STUDENT_BENEFIT = "student_benefit"  # a plan or discount gated on student status
    SOFTWARE = "software"
    CLOUD_CREDITS = "cloud_credits"
    AI_TOOL = "ai_tool"
    DEVELOPER_TOOL = "developer_tool"

    # Funding
    SCHOLARSHIP = "scholarship"
    GRANT = "grant"


class CostType(str, Enum):
    FREE = "free"
    FREE_FOR_STUDENTS = "free_for_students"
    DISCOUNTED = "discounted"
    PAID = "paid"
    FREEMIUM = "freemium"          # free tier, paid upgrade
    SUBSCRIPTION = "subscription"  # recurring fee
    EXAM_FEE = "exam_fee"          # learning is free, sitting the exam is not
    # Used when the official page does not publish a price. The interface says
    # "Cost not confirmed" rather than guessing at one.
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    """How much confidence the product may express about a record.

    The vocabulary is deliberately modest. "Curated" is the strongest claim a
    hand-built catalogue can honestly make: a person wrote the record against
    the official page, but nothing re-checks it afterwards. SOURCE_CHECKED is
    reserved for records a checker actually fetched, and no code path sets it
    until source checking exists.
    """

    CURATED = "curated"              # written by hand from the official page
    SOURCE_CHECKED = "source_checked"  # the official source was fetched and confirmed
    NEEDS_REVIEW = "needs_review"    # not confirmed by anyone yet
    EXPIRED = "expired"              # closed, or the deadline has passed
    REJECTED = "rejected"            # a reviewer rejected it; never shown to students


class VerificationMethod(str, Enum):
    """How the current ``verification_status`` was arrived at."""

    NONE = "none"
    CURATION = "curation"          # a person wrote it from the official page
    HUMAN_REVIEW = "human_review"  # a reviewer confirmed it in the review queue
    SOURCE_FETCH = "source_fetch"  # an automated fetch of the official source
    AUTOMATED = "automated"        # inferred by the extraction pipeline


class DataOrigin(str, Enum):
    """Separates hand-curated seed records from records produced by ingestion.

    The UI never presents SEED data as independently verified.
    """

    SEED = "seed"
    INGESTED = "ingested"
    MANUAL = "manual"


class SourceType(str, Enum):
    OFFICIAL_API = "official_api"
    RSS = "rss"
    ATOM = "atom"
    WEB = "web"
    SOCIAL_SIGNAL = "social_signal"
    MANUAL = "manual"


class ReviewAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class RemotePreference(str, Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    ANY = "any"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    BROWSER = "browser"
    TELEGRAM = "telegram"
    EXTENSION = "extension"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class DestinationType(str, Enum):
    """Which of a record's two URLs the primary call to action points at.

    Derived, never stored: a record has a direct destination or it does not.
    Present so the UI and any future click tracking can name what was offered
    without re-deriving the rule.
    """

    DIRECT_DESTINATION = "direct_destination"
    OFFICIAL_SOURCE = "official_source"


class DestinationAction(str, Enum):
    """What the student is about to do, which sets the button's wording.

    Derived from ``opportunity_type`` so the two can never disagree — a record
    typed as an exam cannot end up saying "Start course". ``VISIT_SOURCE`` is
    the honest fallback when no direct destination could be established.
    """

    START_COURSE = "start_course"
    ENROLL = "enroll"
    START_LEARNING = "start_learning"
    REGISTER_EXAM = "register_exam"
    VIEW_CERTIFICATION = "view_certification"
    GET_ACCESS = "get_access"
    APPLY = "apply"
    REGISTER = "register"
    VISIT_SOURCE = "visit_source"


class UrlCheckStatus(str, Enum):
    """Result of the last time a URL was fetched.

    ``BLOCKED`` matters: several providers reject non-browser clients with 403.
    That is not a broken link, and conflating the two would send reviewers
    chasing pages that work perfectly for a student.
    """

    OK = "ok"
    BLOCKED = "blocked"          # refused our client (403/429); fine in a browser
    UNREACHABLE = "unreachable"  # could not connect; inconclusive
    BROKEN = "broken"            # resolved to 404 or a redirect loop
    UNCHECKED = "unchecked"


# One action per opportunity type. Anything unmapped falls back to VISIT_SOURCE.
DESTINATION_ACTION_BY_TYPE: dict[str, DestinationAction] = {
    OpportunityType.COURSE.value: DestinationAction.START_COURSE,
    OpportunityType.CERTIFICATION.value: DestinationAction.ENROLL,
    OpportunityType.CREDENTIAL.value: DestinationAction.VIEW_CERTIFICATION,
    OpportunityType.EXAM.value: DestinationAction.REGISTER_EXAM,
    OpportunityType.LEARNING_PLATFORM.value: DestinationAction.START_LEARNING,
    OpportunityType.TRAINING.value: DestinationAction.START_LEARNING,
    OpportunityType.VOUCHER.value: DestinationAction.GET_ACCESS,
    OpportunityType.INTERNSHIP.value: DestinationAction.APPLY,
    OpportunityType.HACKATHON.value: DestinationAction.REGISTER,
    OpportunityType.COMPETITION.value: DestinationAction.REGISTER,
    OpportunityType.FELLOWSHIP.value: DestinationAction.APPLY,
    OpportunityType.PROGRAM.value: DestinationAction.APPLY,
    OpportunityType.STUDENT_BENEFIT.value: DestinationAction.GET_ACCESS,
    OpportunityType.SOFTWARE.value: DestinationAction.GET_ACCESS,
    OpportunityType.CLOUD_CREDITS.value: DestinationAction.GET_ACCESS,
    OpportunityType.AI_TOOL.value: DestinationAction.GET_ACCESS,
    OpportunityType.DEVELOPER_TOOL.value: DestinationAction.GET_ACCESS,
    OpportunityType.SCHOLARSHIP.value: DestinationAction.APPLY,
    OpportunityType.GRANT.value: DestinationAction.APPLY,
}


# ---------------------------------------------------------------------------
# Credential taxonomy
#
# Certifications are the first vertical built out in depth. These live in a
# category-specific detail table rather than on Opportunity, so the other five
# categories can add their own without widening the shared row.
#
# Every one of these defaults to UNKNOWN. An absent value from a source means
# "the source did not say", never "no" — inferring otherwise is how a catalogue
# starts telling students things that are not true.
# ---------------------------------------------------------------------------


class CredentialType(str, Enum):
    """What the student actually ends up holding.

    The distinctions matter: a course completion certificate is not a
    professional certification, and conflating them misrepresents what an
    employer will recognise.
    """

    PROFESSIONAL_CERTIFICATION = "professional_certification"  # industry credential, usually an exam
    CERTIFICATION_EXAM = "certification_exam"                  # the exam itself
    PROFESSIONAL_CERTIFICATE = "professional_certificate"      # provider programme, e.g. on a MOOC
    UNIVERSITY_CERTIFICATE = "university_certificate"
    COURSE_CERTIFICATE = "course_certificate"
    COMPLETION_CERTIFICATE = "completion_certificate"
    SKILL_BADGE = "skill_badge"
    DIGITAL_CREDENTIAL = "digital_credential"
    MICRO_CREDENTIAL = "micro_credential"
    LEARNING_PROGRAM = "learning_program"
    TRAINING = "training"
    EXAM_PREP = "exam_prep"
    ASSESSMENT = "assessment"
    UNKNOWN = "unknown"


class AssessmentType(str, Enum):
    PROCTORED_EXAM = "proctored_exam"
    NON_PROCTORED_EXAM = "non_proctored_exam"
    PROJECT = "project"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    COURSE_COMPLETION = "course_completion"
    PRACTICAL_EXAM = "practical_exam"
    PERFORMANCE_BASED = "performance_based"
    NONE = "none"
    UNKNOWN = "unknown"


class ProctoredStatus(str, Enum):
    """Whether the assessment is supervised.

    ``UNKNOWN`` is never collapsed to ``NO``: telling a student an exam is
    unproctored when nobody checked is a materially misleading claim.
    """

    YES = "yes"
    NO = "no"
    OPTIONAL = "optional"
    UNKNOWN = "unknown"


class DeliveryMode(str, Enum):
    ONLINE = "online"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"
    SELF_PACED = "self_paced"
    TEST_CENTRE = "test_centre"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    UNKNOWN = "unknown"


class Specialization(str, Enum):
    """Subject areas, kept extensible — add members as the catalogue grows."""

    CLOUD = "cloud"
    AWS = "aws"
    AZURE = "azure"
    GOOGLE_CLOUD = "google_cloud"
    DEVOPS = "devops"
    KUBERNETES = "kubernetes"
    LINUX = "linux"
    NETWORKING = "networking"
    CYBERSECURITY = "cybersecurity"
    C_CPP = "c_cpp"
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    WEB_DEVELOPMENT = "web_development"
    DATA_SCIENCE = "data_science"
    DATA_ANALYTICS = "data_analytics"
    AI = "ai"
    MACHINE_LEARNING = "machine_learning"
    GENERATIVE_AI = "generative_ai"
    LLM = "llm"
    MLOPS = "mlops"
    DATA_ENGINEERING = "data_engineering"
    DATABASES = "databases"
    SQL = "sql"
    GIT_GITHUB = "git_github"
    SYSTEM_DESIGN = "system_design"
    IOT = "iot"
    EMBEDDED = "embedded"
    UI_UX = "ui_ux"
    PRODUCT = "product"
    DIGITAL_MARKETING = "digital_marketing"
    DESIGN_CAD = "design_cad"
    SALESFORCE = "salesforce"
    SAP = "sap"
    SERVICENOW = "servicenow"


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------


class SourceAuthority(str, Enum):
    """How much weight a source's claims carry.

    Only an authoritative source can support SOURCE_CHECKED. A third-party
    listing is useful for *discovering* that something exists; it is not
    evidence of what it costs or who may apply.
    """

    OFFICIAL_ISSUER = "official_issuer"              # the body that awards the credential
    OFFICIAL_ORGANIZATION = "official_organization"  # the organisation running it
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    PROFESSIONAL_BODY = "professional_body"
    ESTABLISHED_PLATFORM = "established_platform"
    OTHER_REPUTABLE_SOURCE = "other_reputable_source"
    UNKNOWN = "unknown"


#: Authorities whose word is enough to publish a record as source-checked.
AUTHORITATIVE_SOURCES: frozenset[str] = frozenset(
    {
        SourceAuthority.OFFICIAL_ISSUER.value,
        SourceAuthority.OFFICIAL_ORGANIZATION.value,
        SourceAuthority.GOVERNMENT.value,
        SourceAuthority.UNIVERSITY.value,
        SourceAuthority.PROFESSIONAL_BODY.value,
    }
)


class DiscoveryMethod(str, Enum):
    """How a source is read, in order of preference.

    Earlier members are cheaper, more reliable and more clearly permitted than
    later ones. ``UNKNOWN`` means we have not established what a source offers —
    it is never assumed to have an API.
    """

    OFFICIAL_API = "official_api"
    RSS = "rss"
    ATOM = "atom"
    SITEMAP = "sitemap"
    STRUCTURED_DATA = "structured_data"   # JSON-LD / microdata on a public page
    PUBLIC_WEBPAGE = "public_webpage"
    MANUAL = "manual"
    UNKNOWN = "unknown"


#: Preference order used when a source supports more than one method.
DISCOVERY_PREFERENCE: tuple[str, ...] = (
    DiscoveryMethod.OFFICIAL_API.value,
    DiscoveryMethod.RSS.value,
    DiscoveryMethod.ATOM.value,
    DiscoveryMethod.SITEMAP.value,
    DiscoveryMethod.STRUCTURED_DATA.value,
    DiscoveryMethod.PUBLIC_WEBPAGE.value,
    DiscoveryMethod.MANUAL.value,
)


class CheckFrequency(str, Enum):
    HIGH = "high"      # ~6 hours
    NORMAL = "normal"  # ~24 hours
    LOW = "low"        # ~7 days


CHECK_FREQUENCY_MINUTES: dict[str, int] = {
    CheckFrequency.HIGH.value: 6 * 60,
    CheckFrequency.NORMAL.value: 24 * 60,
    CheckFrequency.LOW.value: 7 * 24 * 60,
}


class ChangeKind(str, Enum):
    """Outcome of comparing a source item against what we already hold."""

    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    REMOVED = "removed"
    EXPIRED = "expired"
    FAILED = "failed"
