"""Credential facts for the certification catalogue.

EDITORIAL RULE, same as the rest of the catalogue: only what the official page
states. Every field left out of a record below stays UNKNOWN, and UNKNOWN is a
real answer — it means nobody checked, not that the answer is "no".

In particular:
  * ``proctored`` is omitted wherever the provider does not say. It is never
    set to NO on the grounds that a course "looks" unproctored.
  * ``cost`` distinguishes free learning from a paid exam. AWS publishes free
    training and charges for the exam, so that is EXAM_FEE, not FREE.
  * ``credential_type`` describes what the student ends up holding. Most of
    these issue a completion certificate or a skill badge, not a professional
    certification, and saying otherwise would misrepresent them to employers.
"""
from __future__ import annotations

from app.models.enums import (
    AssessmentType,
    CostType,
    CredentialType,
    DeliveryMode,
    ExperienceLevel,
    ProctoredStatus,
    Specialization,
)

#: Keyed by opportunity title. Absent keys stay at their UNKNOWN defaults.
CREDENTIAL_FACTS: dict[str, dict] = {
    "freeCodeCamp Developer Certifications": dict(
        credential_type=CredentialType.COURSE_CERTIFICATE,
        specializations=[
            Specialization.WEB_DEVELOPMENT,
            Specialization.JAVASCRIPT,
            Specialization.PYTHON,
            Specialization.DATA_ANALYTICS,
        ],
        issuer="freeCodeCamp",
        assessment_type=AssessmentType.PROJECT,
        # freeCodeCamp states certifications are earned by building projects;
        # it does not describe any supervision, so proctoring stays UNKNOWN.
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
    ),
    "Google Cloud Skills Boost": dict(
        credential_type=CredentialType.LEARNING_PROGRAM,
        specializations=[
            Specialization.CLOUD,
            Specialization.GOOGLE_CLOUD,
            Specialization.KUBERNETES,
            Specialization.DATA_ENGINEERING,
        ],
        issuer="Google Cloud",
        assessment_type=AssessmentType.COURSE_COMPLETION,
        delivery_mode=DeliveryMode.ONLINE,
        # A catalogue spanning every level, so no single level applies.
    ),
    "Microsoft Learn Training and Certifications": dict(
        credential_type=CredentialType.LEARNING_PROGRAM,
        specializations=[
            Specialization.CLOUD,
            Specialization.AZURE,
            Specialization.CYBERSECURITY,
        ],
        issuer="Microsoft",
        assessment_type=AssessmentType.COURSE_COMPLETION,
        delivery_mode=DeliveryMode.SELF_PACED,
        # Training is free; the certification exams behind it are paid.
        cost=CostType.EXAM_FEE,
    ),
    "AWS Certified Cloud Practitioner": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.CLOUD, Specialization.AWS],
        issuer="Amazon Web Services",
        exam_code="CLF-C02",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        # AWS states the exam is delivered at a test centre or online-proctored.
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
        # AWS publishes a three-year validity for its certifications.
        validity_months=36,
    ),
    "Cisco Networking Academy — Skills for All": dict(
        credential_type=CredentialType.SKILL_BADGE,
        specializations=[
            Specialization.NETWORKING,
            Specialization.CYBERSECURITY,
            Specialization.PYTHON,
            Specialization.LINUX,
        ],
        issuer="Cisco",
        assessment_type=AssessmentType.COURSE_COMPLETION,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
    ),
    "IBM SkillsBuild": dict(
        credential_type=CredentialType.DIGITAL_CREDENTIAL,
        specializations=[
            Specialization.AI,
            Specialization.DATA_ANALYTICS,
            Specialization.CLOUD,
            Specialization.CYBERSECURITY,
        ],
        issuer="IBM",
        assessment_type=AssessmentType.COURSE_COMPLETION,
        delivery_mode=DeliveryMode.SELF_PACED,
    ),
    "HubSpot Academy Certifications": dict(
        credential_type=CredentialType.COURSE_CERTIFICATE,
        specializations=[Specialization.DIGITAL_MARKETING, Specialization.PRODUCT],
        issuer="HubSpot",
        assessment_type=AssessmentType.QUIZ,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
    ),
    "Kaggle Learn Micro-Courses": dict(
        credential_type=CredentialType.COMPLETION_CERTIFICATE,
        specializations=[
            Specialization.PYTHON,
            Specialization.DATA_SCIENCE,
            Specialization.MACHINE_LEARNING,
            Specialization.SQL,
        ],
        issuer="Kaggle",
        assessment_type=AssessmentType.ASSIGNMENT,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
    ),
    "NVIDIA Deep Learning Institute": dict(
        credential_type=CredentialType.TRAINING,
        specializations=[
            Specialization.AI,
            Specialization.MACHINE_LEARNING,
            Specialization.GENERATIVE_AI,
            Specialization.PYTHON,
        ],
        issuer="NVIDIA",
        delivery_mode=DeliveryMode.ONLINE,
        # Some courses are free, workshops are paid — a mixed catalogue.
        cost=CostType.FREEMIUM,
    ),
    "Google Digital Garage — Fundamentals of Digital Marketing": dict(
        credential_type=CredentialType.COURSE_CERTIFICATE,
        specializations=[Specialization.DIGITAL_MARKETING],
        issuer="Google",
        assessment_type=AssessmentType.QUIZ,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
    ),
}
