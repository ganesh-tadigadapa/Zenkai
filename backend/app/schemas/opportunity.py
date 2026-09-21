from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import (
    AssessmentType,
    Category,
    CostType,
    CredentialType,
    DeliveryMode,
    DataOrigin,
    DestinationAction,
    DestinationType,
    ExperienceLevel,
    OpportunityType,
    ProctoredStatus,
    UrlCheckStatus,
    VerificationMethod,
    VerificationStatus,
)


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    website: str | None = None
    logo_url: str | None = None
    description: str | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    url: str
    source_type: str
    trust_level: int
    last_checked_at: datetime | None = None


class CredentialOut(BaseModel):
    """Certification-specific facts.

    Every field can be UNKNOWN, and UNKNOWN means the official page did not say
    — never that the answer is "no". The UI renders those as "Not stated"
    rather than hiding them, so a student can see what has and has not been
    established.
    """

    model_config = ConfigDict(from_attributes=True)

    credential_type: CredentialType = CredentialType.UNKNOWN
    specializations: list[str] = []
    issuer: str | None = None
    exam_code: str | None = None
    assessment_type: AssessmentType = AssessmentType.UNKNOWN
    proctored_status: ProctoredStatus = ProctoredStatus.UNKNOWN
    delivery_mode: DeliveryMode = DeliveryMode.UNKNOWN
    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN
    duration_hours: int | None = None
    validity_months: int | None = None
    available_countries: list[str] = []


class DestinationOut(BaseModel):
    """The resolved primary call to action.

    ``is_fallback`` is true when no exact enrol/apply page could be established
    and the button points at the provider's own page instead. ``type`` and
    ``action`` exist so future click tracking can record what was offered
    without re-deriving the rule.
    """

    url: str
    type: DestinationType
    action: DestinationAction
    label: str
    is_fallback: bool


class MatchReason(BaseModel):
    label: str
    detail: str
    points: int


class MatchOut(BaseModel):
    score: int = Field(ge=0, le=100)
    reasons: list[MatchReason] = []


class OpportunityBase(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    category: Category
    opportunity_type: OpportunityType
    summary: str = Field(min_length=10, max_length=400)
    description: str = Field(min_length=10)
    eligibility: str | None = None
    who_can_apply: list[str] = []
    location: str = "Global"
    is_remote: bool = True
    cost_type: CostType = CostType.FREE
    cost_amount: float | None = None
    currency: str | None = None
    deadline: datetime | None = None
    is_rolling: bool = False
    deadline_is_estimated: bool = False
    application_url: HttpUrl
    source_url: HttpUrl
    skills: list[str] = []
    tags: list[str] = []
    benefits: list[str] = []
    secondary_categories: list[Category] = []
    #: Exact page where the student can act. Leave unset when it is not known —
    #: the interface falls back to the source rather than guessing.
    direct_destination_url: HttpUrl | None = None
    destination_action: DestinationAction | None = None


class OpportunityCreate(OpportunityBase):
    organization_name: str
    organization_website: str | None = None
    source_id: str | None = None
    verification_status: VerificationStatus = VerificationStatus.NEEDS_REVIEW
    verification_method: VerificationMethod = VerificationMethod.NONE
    data_origin: DataOrigin = DataOrigin.MANUAL
    confidence: float = Field(default=0.5, ge=0, le=1)
    published_at: datetime | None = None


class OpportunityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    summary: str | None = Field(default=None, min_length=10, max_length=400)
    description: str | None = None
    eligibility: str | None = None
    deadline: datetime | None = None
    location: str | None = None
    is_remote: bool | None = None
    cost_type: CostType | None = None
    category: Category | None = None
    opportunity_type: OpportunityType | None = None
    skills: list[str] | None = None
    tags: list[str] | None = None
    benefits: list[str] | None = None


class OpportunityOut(BaseModel):
    """Card-level payload — everything the feed renders, nothing more."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    summary: str
    category: Category
    opportunity_type: OpportunityType
    organization: OrganizationOut
    location: str
    is_remote: bool
    cost_type: CostType
    cost_amount: float | None
    currency: str | None
    deadline: datetime | None
    is_rolling: bool
    deadline_is_estimated: bool = False
    days_left: int | None = None
    # The card links straight to the useful page, so a student never has to
    # search a provider's site from the feed.
    destination: DestinationOut
    application_url: str
    source_url: str
    direct_destination_url: str | None = None
    skills: list[str]
    tags: list[str]
    verification_status: VerificationStatus
    verification_method: VerificationMethod = VerificationMethod.NONE
    data_origin: DataOrigin
    last_checked_at: datetime | None
    discovered_at: datetime
    published_at: datetime | None = None
    updated_at: datetime
    is_saved: bool = False
    match: MatchOut | None = None
    credential: CredentialOut | None = None


class OpportunityDetailOut(OpportunityOut):
    description: str
    eligibility: str | None
    who_can_apply: list[str]
    benefits: list[str]
    secondary_categories: list[Category] = []
    source: SourceOut | None = None
    url_check_status: UrlCheckStatus = UrlCheckStatus.UNCHECKED
    last_url_checked_at: datetime | None = None
    confidence: float
    verified_at: datetime | None
    verified_by: str | None


class OpportunityAdminOut(OpportunityDetailOut):
    content_hash: str
