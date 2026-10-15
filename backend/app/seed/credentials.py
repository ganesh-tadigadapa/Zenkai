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
    "AWS Certified Solutions Architect — Associate": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.CLOUD,
            Specialization.AWS,
            Specialization.SYSTEM_DESIGN,
            Specialization.NETWORKING,
        ],
        issuer="Amazon Web Services",
        exam_code="SAA-C03",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        validity_months=36,
    ),
    "AWS Certified AI Practitioner": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.AI,
            Specialization.MACHINE_LEARNING,
            Specialization.GENERATIVE_AI,
            Specialization.AWS,
        ],
        issuer="Amazon Web Services",
        exam_code="AIF-C01",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
        validity_months=36,
    ),
    "Microsoft Certified: Azure Fundamentals (AZ-900)": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.CLOUD, Specialization.AZURE],
        issuer="Microsoft",
        exam_code="AZ-900",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
        # Microsoft states its fundamentals certifications do not expire.
    ),
    "Microsoft Certified: Azure AI Fundamentals (AI-900)": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.AI,
            Specialization.MACHINE_LEARNING,
            Specialization.AZURE,
        ],
        issuer="Microsoft",
        exam_code="AI-900",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
    ),
    "Google Cloud Associate Cloud Engineer": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.CLOUD,
            Specialization.GOOGLE_CLOUD,
            Specialization.KUBERNETES,
            Specialization.DEVOPS,
        ],
        issuer="Google Cloud",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        # Google publishes a three-year validity for its associate certification.
        validity_months=36,
    ),
    "Google Data Analytics Professional Certificate": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATE,
        specializations=[
            Specialization.DATA_ANALYTICS,
            Specialization.SQL,
            Specialization.DATA_SCIENCE,
        ],
        issuer="Google",
        assessment_type=AssessmentType.COURSE_COMPLETION,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.SUBSCRIPTION,
    ),
    "Meta Front-End Developer Professional Certificate": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATE,
        specializations=[
            Specialization.WEB_DEVELOPMENT,
            Specialization.JAVASCRIPT,
            Specialization.UI_UX,
        ],
        issuer="Meta",
        assessment_type=AssessmentType.PROJECT,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.SUBSCRIPTION,
    ),
    "IBM Data Science Professional Certificate": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATE,
        specializations=[
            Specialization.DATA_SCIENCE,
            Specialization.PYTHON,
            Specialization.SQL,
            Specialization.MACHINE_LEARNING,
        ],
        issuer="IBM",
        assessment_type=AssessmentType.PROJECT,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.SUBSCRIPTION,
    ),
    "DeepLearning.AI Machine Learning Specialization": dict(
        credential_type=CredentialType.COURSE_CERTIFICATE,
        specializations=[
            Specialization.MACHINE_LEARNING,
            Specialization.AI,
            Specialization.PYTHON,
        ],
        issuer="DeepLearning.AI",
        assessment_type=AssessmentType.ASSIGNMENT,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        # Auditing is free; the certificate sits behind a Coursera subscription.
        cost=CostType.FREEMIUM,
    ),
    "Harvard CS50x — Introduction to Computer Science": dict(
        credential_type=CredentialType.COURSE_CERTIFICATE,
        specializations=[
            Specialization.C_CPP,
            Specialization.PYTHON,
            Specialization.SQL,
            Specialization.WEB_DEVELOPMENT,
        ],
        issuer="Harvard University",
        assessment_type=AssessmentType.PROJECT,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.FREEMIUM,
    ),
    "CompTIA Security+": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.CYBERSECURITY, Specialization.NETWORKING],
        issuer="CompTIA",
        exam_code="SY0-701",
        assessment_type=AssessmentType.PERFORMANCE_BASED,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        # CompTIA publishes a three-year renewal cycle for Security+.
        validity_months=36,
    ),
    "CompTIA A+": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.NETWORKING, Specialization.CYBERSECURITY],
        issuer="CompTIA",
        assessment_type=AssessmentType.PERFORMANCE_BASED,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
        validity_months=36,
    ),
    "Cisco Certified Network Associate (CCNA)": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.NETWORKING,
            Specialization.CYBERSECURITY,
            Specialization.PYTHON,
        ],
        issuer="Cisco",
        exam_code="200-301",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.TEST_CENTRE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        # Cisco publishes a three-year validity for associate certifications.
        validity_months=36,
    ),
    "Red Hat Certified System Administrator (RHCSA)": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.LINUX, Specialization.DEVOPS],
        issuer="Red Hat",
        exam_code="EX200",
        assessment_type=AssessmentType.PRACTICAL_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        # Red Hat publishes a three-year validity for its certifications.
        validity_months=36,
    ),
    "Certified Kubernetes Administrator (CKA)": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.KUBERNETES,
            Specialization.DEVOPS,
            Specialization.LINUX,
            Specialization.CLOUD,
        ],
        issuer="The Linux Foundation",
        assessment_type=AssessmentType.PERFORMANCE_BASED,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        # The Linux Foundation publishes a two-year validity for the CKA.
        validity_months=24,
    ),
    "Linux Foundation — Introduction to Linux (LFS101)": dict(
        credential_type=CredentialType.TRAINING,
        specializations=[Specialization.LINUX],
        issuer="The Linux Foundation",
        assessment_type=AssessmentType.COURSE_COMPLETION,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.FREE,
    ),
    "HashiCorp Certified: Terraform Associate": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[
            Specialization.DEVOPS,
            Specialization.CLOUD,
            Specialization.SYSTEM_DESIGN,
        ],
        issuer="HashiCorp",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
        # HashiCorp publishes a two-year validity for its certifications.
        validity_months=24,
    ),
    "Salesforce Trailhead": dict(
        credential_type=CredentialType.LEARNING_PROGRAM,
        specializations=[Specialization.SALESFORCE, Specialization.PRODUCT],
        issuer="Salesforce",
        assessment_type=AssessmentType.ASSIGNMENT,
        delivery_mode=DeliveryMode.SELF_PACED,
        cost=CostType.FREE,
    ),
    "Salesforce Certified Administrator": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.SALESFORCE],
        issuer="Salesforce",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
    ),
    "GitHub Foundations Certification": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.GIT_GITHUB, Specialization.DEVOPS],
        issuer="GitHub",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.EXAM_FEE,
    ),
    "MongoDB Associate Developer Certification": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.DATABASES, Specialization.WEB_DEVELOPMENT],
        issuer="MongoDB",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        cost=CostType.EXAM_FEE,
    ),
    "Postman API Fundamentals Student Expert": dict(
        credential_type=CredentialType.SKILL_BADGE,
        specializations=[Specialization.WEB_DEVELOPMENT, Specialization.SYSTEM_DESIGN],
        issuer="Postman",
        assessment_type=AssessmentType.ASSIGNMENT,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.FREE,
    ),
    "Google Analytics Certification (Skillshop)": dict(
        credential_type=CredentialType.DIGITAL_CREDENTIAL,
        specializations=[Specialization.DIGITAL_MARKETING, Specialization.DATA_ANALYTICS],
        issuer="Google",
        assessment_type=AssessmentType.NON_PROCTORED_EXAM,
        delivery_mode=DeliveryMode.ONLINE,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.FREE,
    ),
    "NPTEL Online Certification": dict(
        credential_type=CredentialType.UNIVERSITY_CERTIFICATE,
        specializations=[
            Specialization.PYTHON,
            Specialization.DATA_SCIENCE,
            Specialization.SYSTEM_DESIGN,
            Specialization.EMBEDDED,
        ],
        issuer="NPTEL (IIT/IISc)",
        assessment_type=AssessmentType.PROCTORED_EXAM,
        proctored=ProctoredStatus.YES,
        # The course runs online; the certification exam is sat in person.
        delivery_mode=DeliveryMode.HYBRID,
        cost=CostType.EXAM_FEE,
    ),
    "Fortinet Certified Fundamentals in Cybersecurity": dict(
        credential_type=CredentialType.PROFESSIONAL_CERTIFICATION,
        specializations=[Specialization.CYBERSECURITY, Specialization.NETWORKING],
        issuer="Fortinet",
        assessment_type=AssessmentType.NON_PROCTORED_EXAM,
        delivery_mode=DeliveryMode.SELF_PACED,
        experience_level=ExperienceLevel.BEGINNER,
        cost=CostType.FREE,
    ),
}
