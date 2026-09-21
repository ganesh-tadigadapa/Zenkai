"""The ingestion pipeline, wired end to end.

    SOURCE -> DISCOVERY -> INGESTION -> EXTRACTION -> DEDUPLICATION
           -> CLASSIFICATION -> VERIFICATION -> HUMAN REVIEW -> DATABASE

Every stage above is implemented and tested against the stub AI client. The only
missing piece is the network fetch inside each connector, which is deliberately
left unimplemented (see app/ingestion/connectors/).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.base import ExtractedOpportunity, RawDocument
from app.ingestion.connectors import connector_for
from app.ingestion.deduplication import DeduplicationService
from app.ingestion.extraction import OpportunityExtractor
from app.ingestion.monitoring import classify, is_result_plausible
from app.ingestion.relevance import assess
from app.ingestion.verification import VerificationService
from app.models.enums import (
    Category,
    ChangeKind,
    CostType,
    DataOrigin,
    OpportunityType,
    VerificationStatus,
)

#: When an extractor does not state a type, fall back to the one implied by the
#: category rather than labelling everything a programme.
DEFAULT_TYPE_BY_CATEGORY: dict[str, str] = {
    Category.INTERNSHIPS.value: OpportunityType.INTERNSHIP.value,
    Category.HACKATHONS.value: OpportunityType.HACKATHON.value,
    Category.SCHOLARSHIPS.value: OpportunityType.SCHOLARSHIP.value,
    Category.CERTIFICATIONS.value: OpportunityType.CERTIFICATION.value,
    Category.TECH_BENEFITS.value: OpportunityType.STUDENT_BENEFIT.value,
    Category.PROGRAMS.value: OpportunityType.PROGRAM.value,
}
from app.models.opportunity import Opportunity, content_fingerprint
from app.models.provenance import (
    OpportunityProvenance,
    RawSourceDocument,
    SourceCheck,
    content_digest,
)
from app.models.source import Source
from app.services.opportunity_service import get_or_create_organization, unique_slug

logger = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    source_id: str | None = None
    fetched: int = 0
    extracted: int = 0
    duplicates: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    #: Entries the relevance gate declined to treat as opportunities. Most of a
    #: real feed lands here, and that is the gate working.
    irrelevant: int = 0
    errors: list[str] = field(default_factory=list)
    #: Set when the mass-deletion guard refused to trust the run's results.
    blocked_reason: str | None = None


class IngestionPipeline:
    def __init__(
        self,
        extractor: OpportunityExtractor | None = None,
        deduper: DeduplicationService | None = None,
        verifier: VerificationService | None = None,
    ) -> None:
        self.extractor = extractor or OpportunityExtractor()
        self.deduper = deduper or DeduplicationService()
        self.verifier = verifier or VerificationService()

    def run_source(self, db: Session, source: Source) -> IngestionReport:
        """Read one source, recording the attempt whether or not it worked."""
        now = datetime.now(timezone.utc)
        check = SourceCheck(source_id=source.id, started_at=now)
        db.add(check)
        db.flush()

        report = IngestionReport(source_id=source.id)
        source.last_checked_at = now

        connector = connector_for(source)
        if connector is None:
            return self._fail(db, source, check, report,
                              f"No connector for source_type={source.source_type}")
        try:
            documents = list(connector.fetch(source))
        except Exception as exc:
            # Every failure mode is recorded, never raised. One source with a
            # broken connector, a refusing host or an unreadable body must not
            # abort a cycle that still has other sources to read.
            return self._fail(
                db, source, check, report, f"{type(exc).__name__}: {exc}"
            )

        report.fetched = len(documents)

        # Before acting on anything, decide whether these results are plausible.
        # A connector returning nothing while we hold records is an outage, not
        # a source that emptied out.
        existing_count = db.scalar(
            select(func.count()).select_from(Opportunity).where(Opportunity.source_id == source.id)
        ) or 0
        verdict = is_result_plausible(len(documents), int(existing_count))
        if not verdict.safe:
            report.blocked_reason = verdict.reason
            return self._fail(db, source, check, report, verdict.reason)

        result = self.process_documents(db, documents, source=source, check=check)
        result.source_id = source.id
        result.fetched = report.fetched

        source.last_success_at = datetime.now(timezone.utc)
        source.consecutive_failures = 0
        check.succeeded = True
        check.finished_at = datetime.now(timezone.utc)
        check.documents_retrieved = result.fetched
        check.candidates_extracted = result.extracted
        check.irrelevant_count = result.irrelevant
        check.created_count = result.created
        check.updated_count = result.updated
        check.unchanged_count = result.unchanged
        check.duplicate_count = result.duplicates
        db.flush()
        return result

    def _fail(
        self,
        db: Session,
        source: Source,
        check: SourceCheck,
        report: IngestionReport,
        reason: str,
    ) -> IngestionReport:
        """Record a failed attempt. Nothing is retired on the strength of one."""
        now = datetime.now(timezone.utc)
        check.succeeded = False
        check.failure_reason = reason
        check.finished_at = now
        check.documents_retrieved = report.fetched
        source.last_failure_at = now
        source.consecutive_failures = (source.consecutive_failures or 0) + 1
        report.errors.append(reason)
        db.flush()
        return report

    def process_documents(
        self,
        db: Session,
        documents: list[RawDocument],
        source: Source | None = None,
        check: SourceCheck | None = None,
    ) -> IngestionReport:
        """Store the evidence, then extract from it.

        Raw documents are persisted first and separately, so a later, better
        extractor can be re-run over them without asking the provider for the
        same pages again.
        """
        report = IngestionReport(fetched=len(documents))

        # Relevance first, before anything is stored or extracted. A vendor's
        # release feed is a hundred product announcements; persisting and
        # extracting all of them would fill the catalogue with things no
        # student can apply to. Rejected entries are counted, not kept — their
        # number is recorded on the check so the ratio stays visible.
        relevant: list[RawDocument] = []
        for document in documents:
            verdict = assess(
                document.title or "",
                document.text or "",
                catalogue=(document.metadata or {}).get("catalogue"),
            )
            if verdict.relevant:
                relevant.append(document)
            else:
                report.irrelevant += 1
                logger.debug(
                    "rejected %r: %s", (document.title or "")[:60], verdict.rejected_because
                )

        stored: list[tuple[RawDocument, RawSourceDocument | None]] = []
        for document in relevant:
            stored.append((document, self._store_raw(db, document, source, check)))

        for document, raw in stored:
            candidate = self.extractor.extract_one(document)
            if candidate is None:
                continue
            report.extracted += 1
            try:
                outcome = self._persist(db, candidate, source, raw)
            except Exception as exc:  # a bad candidate must not abort the batch
                logger.warning("Failed to persist candidate %r: %s", candidate.title, exc)
                report.errors.append(f"{candidate.title}: {exc}")
                continue

            if outcome is ChangeKind.NEW:
                report.created += 1
            elif outcome is ChangeKind.UPDATED:
                report.updated += 1
            elif outcome is ChangeKind.UNCHANGED:
                report.unchanged += 1
            else:
                report.duplicates += 1
        return report

    def _store_raw(
        self,
        db: Session,
        document: RawDocument,
        source: Source | None,
        check: SourceCheck | None,
    ) -> RawSourceDocument | None:
        """Keep what the source returned, before anything interprets it.

        Only non-secret context is recorded: no headers, cookies or
        authorization values ever reach this table.
        """
        if source is None:
            return None
        raw = RawSourceDocument(
            source_id=source.id,
            check_id=check.id if check else None,
            url=document.url,
            title=document.title,
            content=document.text,
            content_hash=content_digest(document.text),
            retrieved_at=document.fetched_at or datetime.now(timezone.utc),
            request_metadata={
                key: value
                for key, value in (document.metadata or {}).items()
                # Belt and braces: never persist anything credential-shaped,
                # even if a connector puts it in metadata by mistake.
                if key.lower() not in {"authorization", "cookie", "set-cookie", "api_key", "token"}
            },
        )
        db.add(raw)
        db.flush()
        return raw

    def _persist(
        self,
        db: Session,
        candidate: ExtractedOpportunity,
        source: Source | None,
        raw: RawSourceDocument | None = None,
    ) -> ChangeKind:
        verdict = self.deduper.check(db, candidate)
        if verdict.is_duplicate:
            existing = db.get(Opportunity, verdict.existing_id)
            if existing is None:
                return ChangeKind.UNCHANGED

            # A second sighting is evidence, not noise. Record what this source
            # said and whether anything moved, rather than discarding it.
            result = classify(existing, self._stated_fields(candidate))
            existing.last_checked_at = datetime.now(timezone.utc)
            self._record_provenance(db, existing, source, raw, result)
            return result.kind

        result = self.verifier.check(candidate, source_trust=source.trust_level if source else 3)

        # Automated discovery never publishes a record as source-checked, however
        # confident the plausibility checks are. Those checks establish that a
        # record is well formed, not that anyone confirmed it against the
        # provider. SOURCE_CHECKED is reserved for a reviewer in the queue or a
        # dedicated re-check against the official page — neither of which is
        # what just happened here.
        unpublished = self._unpublished(candidate)

        status = result.status
        if status is VerificationStatus.SOURCE_CHECKED:
            status = VerificationStatus.NEEDS_REVIEW

        # A verdict may not outlive the evidence behind it. EXPIRED is reached
        # by comparing a deadline against today, so if that deadline came from
        # a field the source does not publish — and was therefore discarded —
        # the verdict goes with it. Otherwise a year mentioned in prose
        # ("Office 2016") marks a currently-available certification as closed
        # and hides it from students.
        if status is VerificationStatus.EXPIRED and "deadline" in unpublished:
            status = VerificationStatus.NEEDS_REVIEW

        category = candidate.category or Category.PROGRAMS.value
        org = get_or_create_organization(db, candidate.organization_name)
        url = candidate.application_url or candidate.source_url or ""

        row = Opportunity(
            title=candidate.title,
            slug=unique_slug(db, candidate.title),
            organization_id=org.id,
            source_id=source.id if source else None,
            category=category,
            opportunity_type=(
                candidate.opportunity_type
                or DEFAULT_TYPE_BY_CATEGORY.get(category, OpportunityType.PROGRAM.value)
            ),
            summary=candidate.summary[:400],
            description=candidate.description,
            eligibility=candidate.eligibility,
            location=candidate.location or "Global",
            is_remote=bool(candidate.is_remote) if candidate.is_remote is not None else True,
            # UNKNOWN, not FREE: an extractor that said nothing about cost has
            # not told us it is free.
            cost_type=(
                CostType.UNKNOWN.value
                if "cost" in unpublished
                else (candidate.cost_type or CostType.UNKNOWN.value)
            ),
            deadline=None if "deadline" in unpublished else candidate.deadline,
            application_url=url,
            source_url=candidate.source_url or url,
            skills=candidate.skills,
            tags=candidate.tags,
            benefits=candidate.benefits,
            verification_status=status.value,
            data_origin=DataOrigin.INGESTED.value,
            confidence=result.confidence,
            content_hash=content_fingerprint(candidate.title, org.name, url),
            last_checked_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.flush()
        self._attach_credential(db, row, candidate)
        self._record_provenance(db, row, source, raw, classify(None, {}))
        return ChangeKind.NEW

    @staticmethod
    def _attach_credential(db: Session, row: Opportunity, candidate) -> None:
        """Record credential facts an adapter established, and nothing more.

        Only fields the source actually carried are written. Cost, proctoring
        and assessment are absent from every catalogue API read so far, so they
        keep their UNKNOWN defaults rather than being inferred from the fact
        that a credential is usually paid and usually proctored.
        """
        metadata = getattr(candidate, "provider_metadata", None) or {}
        adapter_name = metadata.get("adapter")
        if not adapter_name:
            return

        from app.ingestion.adapters import REGISTRY
        from app.models.credential import CredentialDetail

        adapter = next((a for a in REGISTRY if a.name == adapter_name), None)
        if adapter is None or not hasattr(adapter, "credential_type"):
            return

        credential_type = adapter.credential_type(metadata)
        detail = CredentialDetail(
            opportunity_id=row.id,
            credential_type=credential_type.value,
            specializations=adapter.specializations(metadata, row.title),
            issuer=metadata.get("organization") or None,
            exam_code=adapter.exam_code(metadata),
            experience_level=adapter.experience_level(metadata).value,
        )
        db.add(detail)
        db.flush()

    @staticmethod
    def _unpublished(candidate: ExtractedOpportunity) -> set[str]:
        """Fields the source is known not to publish.

        An adapter reading a structured catalogue knows what its API carries.
        That knowledge beats a text heuristic: a certification description
        mentioning "Office 2019" is not a deadline, and one mentioning a
        "discounted voucher" is not the exam price. Where a source does not
        publish a field, the extractor's guess is discarded and the value stays
        UNKNOWN — which is the honest answer.
        """
        raw = (candidate.provider_metadata or {}).get("unpublished_fields", "")
        return {f.strip() for f in raw.split(",") if f.strip()}

    @staticmethod
    def _stated_fields(candidate: ExtractedOpportunity) -> dict:
        """Only what the source actually said.

        An absent key means unmentioned. It must never overwrite a value we
        hold — a source going quiet about a price is not it becoming free.
        """
        stated = {
            "cost_type": candidate.cost_type,
            "deadline": candidate.deadline,
            "eligibility": candidate.eligibility,
            "location": candidate.location,
            "is_remote": candidate.is_remote,
            "summary": candidate.summary or None,
            "source_url": candidate.source_url,
        }
        return {key: value for key, value in stated.items() if value is not None}

    @staticmethod
    def _record_provenance(
        db: Session,
        opportunity: Opportunity,
        source: Source | None,
        raw: RawSourceDocument | None,
        result,
    ) -> None:
        db.add(
            OpportunityProvenance(
                opportunity_id=opportunity.id,
                source_id=source.id if source else None,
                raw_document_id=raw.id if raw else None,
                change_kind=result.kind.value,
                changed_fields=result.as_dict,
            )
        )
        db.flush()

    def run_due_sources(self, db: Session) -> list[IngestionReport]:
        """Entry point the scheduler calls. Only active, permitted sources run."""
        sources = db.scalars(
            select(Source).where(Source.active.is_(True), Source.robots_allowed.is_(True))
        ).all()
        reports = []
        for source in sources:
            try:
                reports.append(self.run_source(db, source))
            except Exception as exc:  # defence in depth; run_source should not raise
                logger.exception("run_source raised for %s", source.name)
                reports.append(
                    IngestionReport(source_id=source.id, errors=[f"{type(exc).__name__}: {exc}"])
                )
        return reports
