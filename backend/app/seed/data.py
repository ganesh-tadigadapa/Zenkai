"""Curated opportunity catalogue.

EDITORIAL RULES — every record in this file must satisfy all of them:

  * The organisation is real and the programme genuinely exists.
  * ``url``/``source_url`` point at the organisation's own official page.
  * Descriptions state only what that official page states. No invented amounts,
    acceptance rates, cohort sizes, stipends or perks.
  * **No invented deadlines.** A date appears only where the programme publishes
    a standing one. Annual programmes whose dates are announced each cycle carry
    no deadline at all, and the interface says "Deadline not listed" rather than
    guessing. ``rolling=True`` is used only where applications genuinely stay
    open continuously.
  * **No invented costs.** Where the price is not published, ``cost`` is left
    unset and the interface says "Cost not confirmed".
  * ``type`` describes what the student actually receives. A catalogue of
    courses is a ``learning_platform``, not a ``certification``; a paid
    credentialing exam is an ``exam``.

Every record is stored with ``data_origin=SEED``.

``status`` values:
  * ``curated``      — written by hand against the official page. This is the
                       strongest claim a hand-built catalogue can make: nobody
                       re-checks it afterwards, and the UI says so.
  * ``needs_review`` — details change often, or could not be confidently
                       established at curation time. Shown to students clearly
                       labelled, and queued for a reviewer.

No record is stored as ``source_checked``. That status is reserved for records
whose official source was actually fetched, and nothing fetches anything yet.
"""
from __future__ import annotations

# fmt: off
TECH_BENEFITS = [
    dict(
        title="GitHub Student Developer Pack",
        org="GitHub", org_url="https://github.com",
        category="tech_benefits", type="student_benefit",
        summary="A bundle of free developer tools and services for verified students.",
        description=(
            "The GitHub Student Developer Pack gives verified students free access to a "
            "collection of developer tools and services from GitHub and its partners, "
            "alongside GitHub Pro. Access is granted for the duration of your studies and "
            "requires verification of student status, typically with a school-issued email "
            "address or proof of enrolment. The exact list of partner offers changes over "
            "time — check the official page for what is currently included."
        ),
        eligibility="Students aged 13 or older enrolled in a degree- or diploma-granting course of study.",
        who_can_apply=["Verified students", "Any field of study"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://education.github.com/pack",
        source_url="https://education.github.com/pack",
        skills=["Git", "GitHub", "Software Engineering"],
        tags=["developer-tools", "free", "student-pack", "version-control"],
        benefits=["GitHub Pro while you are a student", "Partner offers from developer tool vendors"],
        status="curated",
    ),
    dict(
        title="Microsoft Azure for Students",
        org="Microsoft", org_url="https://www.microsoft.com",
        category="tech_benefits", type="cloud_credits",
        summary="Azure cloud credit and access to a set of always-free Azure services, with no credit card required.",
        description=(
            "Azure for Students gives eligible students an Azure credit to spend in the first "
            "12 months plus access to a set of services that are free within monthly limits. "
            "Microsoft states that no credit card is required to activate the offer. Eligibility "
            "is verified through an academic email address or other proof of enrolment. Credit "
            "amounts and included services are set by Microsoft and listed on the official page."
        ),
        eligibility="Students aged 18 or older at an accredited institution, verified via academic email.",
        who_can_apply=["Undergraduate students", "Postgraduate students"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://azure.microsoft.com/en-us/free/students/",
        source_url="https://azure.microsoft.com/en-us/free/students/",
        skills=["Azure", "Cloud", "DevOps"],
        tags=["cloud", "credits", "azure", "free", "infrastructure"],
        benefits=["Azure credit for the first 12 months", "Free tier services within monthly limits"],
        status="curated",
    ),
    dict(
        title="JetBrains Free Educational Licence",
        org="JetBrains", org_url="https://www.jetbrains.com",
        category="tech_benefits", type="software",
        summary="Free access to JetBrains professional IDEs for students and teachers.",
        description=(
            "JetBrains offers students and teachers a free educational licence covering its "
            "professional IDEs, including IntelliJ IDEA Ultimate, PyCharm Professional, WebStorm "
            "and others. The licence is for non-commercial educational use and must be renewed "
            "annually while you remain eligible. Verification is done with a university email "
            "address, ISIC card or official documents."
        ),
        eligibility="Students and teachers at accredited educational institutions; non-commercial use only.",
        who_can_apply=["Students", "Teachers"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://www.jetbrains.com/community/education/#students",
        source_url="https://www.jetbrains.com/community/education/#students",
        skills=["Java", "Python", "JavaScript", "Kotlin"],
        tags=["ide", "developer-tools", "free", "software"],
        benefits=["All JetBrains professional IDEs", "Renewable annually while enrolled"],
        status="curated",
    ),
    dict(
        title="Figma Education Plan",
        org="Figma", org_url="https://www.figma.com",
        category="tech_benefits", type="software",
        summary="Free Figma and FigJam features for verified students and educators.",
        description=(
            "Figma's education plan gives verified students and educators access to a set of "
            "paid Figma and FigJam features at no cost, for educational use. Applicants verify "
            "their status through Figma's education application form; the plan is time-limited "
            "and renewable while you remain eligible. Feature inclusions are listed on Figma's "
            "education page."
        ),
        eligibility="Students and educators enrolled at an accredited institution, using Figma for coursework.",
        who_can_apply=["Design students", "Educators"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://www.figma.com/education/",
        source_url="https://www.figma.com/education/",
        skills=["UI Design", "UX Design", "Prototyping", "Figma"],
        tags=["design", "free", "collaboration", "product-design"],
        benefits=["Paid Figma features for education use", "FigJam for collaborative work"],
        status="curated",
    ),
    dict(
        title="Notion for Education",
        org="Notion", org_url="https://www.notion.so",
        category="tech_benefits", type="software",
        summary="A free Notion plan for students and educators with an academic email address.",
        description=(
            "Notion offers students and educators a free upgraded personal plan when they sign "
            "up or verify with an eligible academic email address. The offer is intended for "
            "individual academic use. Notion sets which plan and features are included; see the "
            "official education page for current terms."
        ),
        eligibility="Students and educators with a verified academic email address.",
        who_can_apply=["Students", "Educators"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://www.notion.com/product/notion-for-education",
        source_url="https://www.notion.com/product/notion-for-education",
        skills=["Productivity", "Documentation", "Note Taking"],
        tags=["productivity", "free", "notes", "organisation"],
        benefits=["Free upgraded personal plan", "Academic templates"],
        status="curated",
    ),
    dict(
        title="Autodesk Education Access",
        org="Autodesk", org_url="https://www.autodesk.com",
        category="tech_benefits", type="software",
        summary="Free educational licences for Autodesk design and engineering software.",
        description=(
            "Autodesk provides free educational access to products such as AutoCAD, Fusion and "
            "Revit for eligible students and educators. Licences are for educational use only, "
            "are time-limited, and require verification of academic status. Product availability "
            "varies by region and is listed on the Autodesk Education site."
        ),
        eligibility="Students aged 13+ and educators at a qualified educational institution; educational use only.",
        who_can_apply=["Engineering students", "Architecture students", "Design students"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://www.autodesk.com/education/edu-software/overview",
        source_url="https://www.autodesk.com/education/edu-software/overview",
        skills=["CAD", "3D Modelling", "Mechanical Design"],
        tags=["engineering", "cad", "free", "design"],
        benefits=["Educational licences for Autodesk products", "Renewable while eligible"],
        status="curated",
    ),
    dict(
        title="Unity Student Plan",
        org="Unity", org_url="https://unity.com",
        category="tech_benefits", type="software",
        summary="Unity's student offering for learning game and real-time 3D development.",
        description=(
            "Unity offers a student plan giving eligible learners access to Unity tooling and "
            "learning resources for educational use. Verification of student status is required "
            "and the plan is subject to Unity's education terms. Check the official page for the "
            "current feature set and eligibility rules in your region."
        ),
        eligibility="Verified students aged 16 or older enrolled at an accredited institution.",
        who_can_apply=["Game development students", "Computer science students"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://unity.com/products/unity-student",
        source_url="https://unity.com/products/unity-student",
        skills=["Unity", "C#", "Game Development", "3D"],
        tags=["game-dev", "free", "3d", "software"],
        benefits=["Unity student licence", "Access to Unity Learn content"],
        status="curated",
    ),
    dict(
        title="Google Cloud Free Tier",
        org="Google Cloud", org_url="https://cloud.google.com",
        category="tech_benefits", type="cloud_credits",
        summary="Free trial credit plus a set of always-free Google Cloud products.",
        description=(
            "Google Cloud's Free Tier combines a time-limited trial credit for new accounts with "
            "a set of products that remain free within monthly usage limits. It is open to anyone, "
            "not only students, and is a common starting point for learning cloud engineering. "
            "Credit amounts, trial length and the always-free product list are defined by Google "
            "and published on the official page."
        ),
        eligibility="Open to new Google Cloud accounts; a billing profile is required for the trial.",
        who_can_apply=["Anyone", "Students learning cloud"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://cloud.google.com/free",
        source_url="https://cloud.google.com/free",
        skills=["Google Cloud", "Cloud", "Kubernetes", "DevOps"],
        tags=["cloud", "credits", "gcp", "free", "infrastructure"],
        benefits=["Trial credit for new accounts", "Always-free product tier within limits"],
        status="curated",
    ),
    dict(
        title="AWS Free Tier",
        org="Amazon Web Services", org_url="https://aws.amazon.com",
        category="tech_benefits", type="cloud_credits",
        summary="Free AWS usage tiers for learning and building on Amazon's cloud.",
        description=(
            "The AWS Free Tier provides free usage allowances across AWS services, split into "
            "always-free offers, 12-month offers for new accounts, and short-term trials. It is "
            "the standard route for students to get hands-on with AWS before a certification. "
            "Exact allowances per service are published by AWS and change over time."
        ),
        eligibility="Open to new and existing AWS accounts, depending on the offer type.",
        who_can_apply=["Anyone", "Students learning cloud"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://aws.amazon.com/free/",
        source_url="https://aws.amazon.com/free/",
        skills=["AWS", "Cloud", "EC2", "S3", "DevOps"],
        tags=["cloud", "credits", "aws", "free", "infrastructure"],
        benefits=["Always-free service allowances", "12-month new-account offers"],
        status="curated",
    ),
    dict(
        title="Postman Student Program",
        org="Postman", org_url="https://www.postman.com",
        category="tech_benefits", type="student_benefit",
        summary="Postman's programme for students learning APIs, including free training paths.",
        description=(
            "The Postman Student Program supports students learning API development with "
            "training content and student-focused resources, including the Student Expert "
            "learning path. Details of what is offered and how to join are on Postman's official "
            "student programme page."
        ),
        eligibility="Students learning API development; see the official page for verification steps.",
        who_can_apply=["Computer science students", "Backend developers"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.postman.com/company/student-program/",
        source_url="https://www.postman.com/company/student-program/",
        skills=["API", "REST", "Postman", "Backend"],
        tags=["api", "developer-tools", "free", "backend"],
        benefits=["Student learning paths", "API training resources"],
        status="curated",
    ),
    dict(
        title="Oracle Cloud Free Tier",
        org="Oracle", org_url="https://www.oracle.com",
        category="tech_benefits", type="cloud_credits",
        summary="Always-free Oracle Cloud Infrastructure services plus a trial credit.",
        description=(
            "Oracle Cloud Free Tier combines always-free OCI services with a time-limited trial "
            "credit for new accounts. Oracle publishes the current list of always-free resources "
            "and the trial terms on the official page; both have changed over time, so confirm "
            "before relying on a specific allowance."
        ),
        eligibility="Open to new Oracle Cloud accounts.",
        who_can_apply=["Anyone", "Students learning cloud"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.oracle.com/cloud/free/",
        source_url="https://www.oracle.com/cloud/free/",
        skills=["Oracle Cloud", "Cloud", "Linux"],
        tags=["cloud", "credits", "free", "infrastructure"],
        benefits=["Always-free OCI resources", "Trial credit for new accounts"],
        status="needs_review",
    ),
    dict(
        title="Adobe Creative Cloud Student Pricing",
        org="Adobe", org_url="https://www.adobe.com",
        category="tech_benefits", type="student_benefit",
        summary="Discounted Creative Cloud subscriptions for eligible students and teachers.",
        description=(
            "Adobe offers Creative Cloud to eligible students and teachers at a reduced "
            "subscription price rather than free. Eligibility requires proof of enrolment or "
            "employment at an eligible institution. Pricing varies by region and by year of "
            "subscription, so check Adobe's official education pricing page for your country."
        ),
        eligibility="Students aged 13+ and teachers at an eligible institution, with proof of status.",
        who_can_apply=["Design students", "Media students", "Teachers"],
        location="Global", remote=True, cost="discounted", rolling=True,
        url="https://www.adobe.com/creativecloud/buy/students.html",
        source_url="https://www.adobe.com/creativecloud/buy/students.html",
        skills=["Photoshop", "Illustrator", "Video Editing", "Design"],
        tags=["design", "discounted", "creative", "software"],
        benefits=["Reduced student pricing on Creative Cloud"],
        status="curated",
    ),
    dict(
        title="Tableau for Students",
        org="Tableau", org_url="https://www.tableau.com",
        category="tech_benefits", type="software",
        summary="A free one-year Tableau licence for verified students, renewable while enrolled.",
        description=(
            "Tableau offers verified students a free licence for Tableau Desktop and Tableau "
            "Prep Builder for a year, renewable while they remain enrolled. The licence is for "
            "non-commercial academic use and requires proof of current enrolment."
        ),
        eligibility="Students enrolled at an accredited academic institution, with proof of enrolment.",
        who_can_apply=["Data science students", "Business students"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://www.tableau.com/academic/students",
        source_url="https://www.tableau.com/academic/students",
        skills=["Data Visualisation", "Analytics", "Tableau", "SQL"],
        tags=["data", "analytics", "free", "visualisation"],
        benefits=["One-year Tableau licence", "Renewable while enrolled"],
        status="curated",
    ),
    dict(
        title="MongoDB Atlas Free Cluster",
        org="MongoDB", org_url="https://www.mongodb.com",
        category="tech_benefits", type="cloud_credits",
        summary="A permanently free MongoDB Atlas tier for learning and small projects.",
        description=(
            "MongoDB Atlas offers a free shared cluster tier that does not expire and requires no "
            "credit card, intended for learning, prototyping and small projects. Storage and "
            "performance limits apply and are published by MongoDB. Students can also access "
            "additional MongoDB learning resources and certification material."
        ),
        eligibility="Open to anyone with a MongoDB Atlas account.",
        who_can_apply=["Anyone", "Students building projects"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.mongodb.com/cloud/atlas/register",
        source_url="https://www.mongodb.com/pricing",
        skills=["MongoDB", "Databases", "Backend", "NoSQL"],
        tags=["database", "free", "backend", "cloud"],
        benefits=["Free shared cluster with no expiry", "No credit card required"],
        status="curated",
    ),
    dict(
        title="DigitalOcean Credits via GitHub Student Pack",
        org="DigitalOcean", org_url="https://www.digitalocean.com",
        category="tech_benefits", type="cloud_credits",
        summary="Hosting credit for students, offered as part of the GitHub Student Developer Pack.",
        description=(
            "DigitalOcean participates in the GitHub Student Developer Pack, offering platform "
            "credit to verified students for hosting projects on Droplets and App Platform. The "
            "credit amount and validity window are set by DigitalOcean and listed in the pack; "
            "you must first be approved for the GitHub Student Developer Pack."
        ),
        eligibility="Students approved for the GitHub Student Developer Pack.",
        who_can_apply=["Students with an approved GitHub Student Pack"],
        location="Global", remote=True, cost="free_for_students", rolling=True,
        url="https://www.digitalocean.com/github-students",
        source_url="https://www.digitalocean.com/github-students",
        skills=["Linux", "Deployment", "DevOps", "Docker"],
        tags=["cloud", "hosting", "credits", "deployment"],
        benefits=["Hosting credit for student projects"],
        status="needs_review",
    ),
    dict(
        title="Google Colab",
        org="Google", org_url="https://research.google.com",
        category="tech_benefits", type="ai_tool",
        summary="Free browser-based notebooks with access to hosted compute for ML work.",
        description=(
            "Google Colab provides hosted Jupyter notebooks in the browser with access to free "
            "compute, subject to usage limits and availability. It is widely used by students "
            "for machine learning coursework and projects because it requires no local GPU. Paid "
            "tiers offer longer runtimes and better hardware; the free tier's limits are set by "
            "Google and can change."
        ),
        eligibility="Open to anyone with a Google account.",
        who_can_apply=["Anyone", "ML students"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://colab.research.google.com/",
        source_url="https://colab.research.google.com/",
        skills=["Python", "Machine Learning", "Jupyter", "AI"],
        tags=["ai", "ml", "free", "notebooks", "compute"],
        benefits=["Hosted notebooks with free compute", "No local setup required"],
        status="curated",
    ),
    dict(
        title="Kaggle Notebooks and Datasets",
        org="Kaggle", org_url="https://www.kaggle.com",
        category="tech_benefits", type="ai_tool",
        summary="Free hosted notebooks with weekly accelerator quota, plus a large public dataset library.",
        description=(
            "Kaggle provides free hosted notebooks with a weekly quota of accelerator time, "
            "alongside a large catalogue of public datasets and community code. It is a practical "
            "environment for students to practise data science without provisioning hardware. "
            "Quotas are set by Kaggle and published in its documentation."
        ),
        eligibility="Open to anyone with a verified Kaggle account.",
        who_can_apply=["Anyone", "Data science students"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.kaggle.com/code",
        source_url="https://www.kaggle.com/docs/notebooks",
        skills=["Python", "Data Science", "Machine Learning", "Pandas"],
        tags=["ai", "ml", "data", "free", "compute"],
        benefits=["Free notebooks with accelerator quota", "Public datasets and community code"],
        status="curated",
    ),
]
# fmt: on


# fmt: off
CERTIFICATIONS = [
    dict(
        title="freeCodeCamp Developer Certifications",
        org="freeCodeCamp", org_url="https://www.freecodecamp.org",
        category="certifications", type="certification",
        summary="Free, project-based certifications in web development, data analysis and more.",
        description=(
            "freeCodeCamp offers a set of free certifications, each earned by completing a series "
            "of lessons and building the required projects. Certifications cover areas such as "
            "responsive web design, JavaScript algorithms and data structures, front-end "
            "libraries, data analysis with Python and machine learning. There is no fee at any "
            "stage and the curriculum is open source."
        ),
        eligibility="Open to anyone. No prerequisites and no fee.",
        who_can_apply=["Anyone", "Self-taught developers", "Students"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.freecodecamp.org/learn",
        source_url="https://www.freecodecamp.org/learn",
        skills=["JavaScript", "HTML", "CSS", "Python", "React"],
        tags=["web-development", "free", "self-paced", "projects"],
        benefits=["Verifiable certification", "Project portfolio you keep"],
        status="curated",
    ),
    dict(
        title="Google Cloud Skills Boost",
        org="Google Cloud", org_url="https://cloud.google.com",
        category="certifications", type="learning_platform",
        summary="Google's official learning platform with hands-on labs and certification paths.",
        description=(
            "Google Cloud Skills Boost hosts Google's official training: guided labs on live "
            "cloud infrastructure, skill badges and learning paths aligned to the Google Cloud "
            "certifications. Some content is free and some requires credits or a subscription. "
            "Google periodically runs no-cost programmes for students and developers; check the "
            "platform for what is currently open."
        ),
        eligibility="Open to anyone with a Google account; some paths require paid credits.",
        who_can_apply=["Cloud learners", "Students", "Professionals"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.cloudskillsboost.google/",
        source_url="https://www.cloudskillsboost.google/",
        skills=["Google Cloud", "Kubernetes", "BigQuery", "Cloud"],
        tags=["cloud", "gcp", "labs", "certification"],
        benefits=["Hands-on labs on real infrastructure", "Skill badges"],
        status="curated",
    ),
    dict(
        title="Microsoft Learn Training and Certifications",
        org="Microsoft", org_url="https://learn.microsoft.com",
        category="certifications", type="learning_platform",
        summary="Free self-paced training for Microsoft certifications, with student exam pricing.",
        description=(
            "Microsoft Learn provides free, self-paced learning paths covering Azure, Microsoft "
            "365, Power Platform and security. The training is free; the certification exams are "
            "paid, though Microsoft offers reduced student pricing on selected fundamentals "
            "exams for eligible learners. Confirm current exam pricing and student eligibility on "
            "the official certification page."
        ),
        eligibility="Training open to all; student exam pricing requires academic verification.",
        who_can_apply=["Students", "Professionals"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://learn.microsoft.com/en-us/training/",
        source_url="https://learn.microsoft.com/en-us/credentials/",
        skills=["Azure", "Cloud", "Security", "Power Platform"],
        tags=["cloud", "azure", "certification", "free-training"],
        benefits=["Free learning paths", "Student pricing on selected exams"],
        status="curated",
    ),
    dict(
        title="AWS Certified Cloud Practitioner",
        org="Amazon Web Services", org_url="https://aws.amazon.com",
        category="certifications", type="exam",
        summary="AWS's entry-level certification covering cloud concepts, security, and billing.",
        description=(
            "The AWS Certified Cloud Practitioner is Amazon's foundational certification, "
            "validating an overall understanding of AWS services, security, architecture and "
            "pricing. AWS publishes free digital training through AWS Skill Builder; the exam "
            "itself is paid. It is commonly the first AWS credential a student takes before the "
            "associate-level exams."
        ),
        eligibility="No formal prerequisites. AWS recommends around six months of AWS exposure.",
        who_can_apply=["Students", "Career changers", "Professionals"],
        location="Global", remote=True, cost="paid", rolling=True,
        url="https://aws.amazon.com/certification/certified-cloud-practitioner/",
        source_url="https://aws.amazon.com/certification/certified-cloud-practitioner/",
        skills=["AWS", "Cloud", "Security", "Architecture"],
        tags=["cloud", "aws", "certification", "entry-level"],
        benefits=["Industry-recognised AWS credential", "Free preparatory training on Skill Builder"],
        status="curated",
    ),
    dict(
        title="Cisco Networking Academy — Skills for All",
        org="Cisco", org_url="https://www.cisco.com",
        category="certifications", type="learning_platform",
        summary="Free Cisco courses in networking, cybersecurity and Python with digital badges.",
        description=(
            "Cisco's Skills for All platform offers free, self-paced courses in networking "
            "fundamentals, cybersecurity and Python programming, with digital badges on "
            "completion. Some paths map towards Cisco's paid professional certifications such as "
            "CCNA. The learning content itself carries no fee."
        ),
        eligibility="Open to anyone. Free registration.",
        who_can_apply=["Anyone", "Students", "Career changers"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://skillsforall.com/",
        source_url="https://skillsforall.com/",
        skills=["Networking", "Cybersecurity", "Python", "Linux"],
        tags=["networking", "security", "free", "badges"],
        benefits=["Free courses and digital badges", "Pathways towards Cisco certifications"],
        status="curated",
    ),
    dict(
        title="IBM SkillsBuild",
        org="IBM", org_url="https://www.ibm.com",
        category="certifications", type="learning_platform",
        summary="Free IBM courses and digital credentials in AI, data, cloud and cybersecurity.",
        description=(
            "IBM SkillsBuild offers free online courses and digital credentials aimed at students "
            "and job seekers, covering artificial intelligence, data analysis, cloud computing, "
            "cybersecurity and professional skills. Credentials are issued as verifiable digital "
            "badges. Course availability varies by region and audience track."
        ),
        eligibility="Open to students and adult learners; free registration.",
        who_can_apply=["Students", "Job seekers"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://skillsbuild.org/",
        source_url="https://skillsbuild.org/",
        skills=["AI", "Data Analysis", "Cloud", "Cybersecurity"],
        tags=["ai", "data", "free", "badges", "cloud"],
        benefits=["Free courses", "Verifiable digital credentials"],
        status="curated",
    ),
    dict(
        title="HubSpot Academy Certifications",
        org="HubSpot", org_url="https://www.hubspot.com",
        category="certifications", type="certification",
        summary="Free certifications in marketing, sales and customer service.",
        description=(
            "HubSpot Academy offers free courses and certifications across inbound marketing, "
            "content marketing, sales enablement, SEO and customer service. Certifications are "
            "earned by completing video lessons and passing an exam, and are widely recognised in "
            "marketing roles. All listed certifications are free."
        ),
        eligibility="Open to anyone with a free HubSpot account.",
        who_can_apply=["Anyone", "Marketing students", "Business students"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://academy.hubspot.com/courses",
        source_url="https://academy.hubspot.com/courses",
        skills=["Marketing", "SEO", "Content", "Sales"],
        tags=["marketing", "free", "business", "certification"],
        benefits=["Free certifications", "Shareable credential badges"],
        status="curated",
    ),
    dict(
        title="Kaggle Learn Micro-Courses",
        org="Kaggle", org_url="https://www.kaggle.com",
        category="certifications", type="course",
        summary="Short, free, hands-on data science courses with completion certificates.",
        description=(
            "Kaggle Learn offers short practical courses in Python, pandas, machine learning, "
            "deep learning, SQL, data visualisation and feature engineering. Each course runs in "
            "a hosted notebook and issues a completion certificate. The courses are free and "
            "designed to be finished in a few hours each."
        ),
        eligibility="Open to anyone with a Kaggle account.",
        who_can_apply=["Anyone", "Data science students"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.kaggle.com/learn",
        source_url="https://www.kaggle.com/learn",
        skills=["Python", "Pandas", "Machine Learning", "SQL"],
        tags=["data", "ml", "free", "self-paced"],
        benefits=["Completion certificates", "Hands-on notebook exercises"],
        status="curated",
    ),
    dict(
        title="NVIDIA Deep Learning Institute",
        org="NVIDIA", org_url="https://www.nvidia.com",
        category="certifications", type="training",
        summary="NVIDIA's training in deep learning and accelerated computing, with some free courses.",
        description=(
            "The NVIDIA Deep Learning Institute provides training in deep learning, data science "
            "and accelerated computing. A subset of courses is available at no cost, while "
            "instructor-led workshops and some certificate courses are paid. NVIDIA also runs "
            "programmes for university students and educators; check the official page for "
            "current free offerings."
        ),
        eligibility="Open to anyone; pricing varies by course. Some university programmes apply.",
        who_can_apply=["AI students", "Researchers", "Professionals"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://www.nvidia.com/en-us/training/",
        source_url="https://www.nvidia.com/en-us/training/",
        skills=["Deep Learning", "CUDA", "AI", "Python"],
        tags=["ai", "deep-learning", "gpu", "certification"],
        benefits=["Selected free self-paced courses", "Certificates of competency on paid courses"],
        status="needs_review",
    ),
    dict(
        title="Google Digital Garage — Fundamentals of Digital Marketing",
        org="Google", org_url="https://www.google.com",
        category="certifications", type="course",
        summary="A free certification course in digital marketing fundamentals.",
        description=(
            "Google's Digital Garage offers a free course in digital marketing fundamentals, "
            "covering search, analytics, social and e-commerce, with a certificate on completion. "
            "It is self-paced and requires no prior experience. Availability and the exact "
            "certificate issuer have changed over time — confirm on the official site."
        ),
        eligibility="Open to anyone; free registration.",
        who_can_apply=["Anyone", "Business students", "Marketing students"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://grow.google/certificates/",
        source_url="https://grow.google/certificates/",
        skills=["Digital Marketing", "Analytics", "SEO"],
        tags=["marketing", "free", "business"],
        benefits=["Free certificate", "Self-paced modules"],
        status="needs_review",
    ),
]
# fmt: on


# fmt: off
INTERNSHIPS = [
    dict(
        title="Google STEP Internship",
        org="Google", org_url="https://www.google.com",
        category="internships", type="internship",
        summary="A paid software engineering internship for first- and second-year undergraduates.",
        description=(
            "STEP (Student Training in Engineering Program) is Google's paid summer internship "
            "aimed at first- and second-year undergraduate students in computer science and "
            "related fields. Interns work on a project with a team and receive mentoring. "
            "Applications open on Google's careers site ahead of each summer; exact windows and "
            "locations vary by region and year."
        ),
        eligibility="First- or second-year undergraduates in computer science or a related field.",
        who_can_apply=["1st year undergraduates", "2nd year undergraduates"],
        location="Multiple locations", remote=False, cost="free",
        url="https://www.google.com/about/careers/applications/jobs/results/?q=STEP%20intern",
        source_url="https://buildyourfuture.withgoogle.com/programs/step",
        skills=["Software Engineering", "Algorithms", "Java", "Python", "C++"],
        tags=["internship", "paid", "software-engineering", "big-tech"],
        benefits=["Paid internship", "Mentorship from Google engineers"],
        status="curated",
    ),
    dict(
        title="Microsoft Explore Internship",
        org="Microsoft", org_url="https://www.microsoft.com",
        category="internships", type="internship",
        summary="A rotational internship for early-career undergraduates across engineering and PM.",
        description=(
            "Microsoft Explore is a rotational internship programme for first- and second-year "
            "undergraduates, giving exposure to software engineering and product management "
            "rather than a single fixed role. Participants work in small teams on a project with "
            "mentoring. Application timing and locations are published on Microsoft's careers "
            "site each cycle."
        ),
        eligibility="First- and second-year undergraduates, typically in computing disciplines.",
        who_can_apply=["1st year undergraduates", "2nd year undergraduates"],
        location="Redmond, USA and other sites", remote=False, cost="free",
        url="https://careers.microsoft.com/students/us/en/usexploreprogram",
        source_url="https://careers.microsoft.com/students/us/en/usexploreprogram",
        skills=["Software Engineering", "Product Management", "C#", "Python"],
        tags=["internship", "paid", "rotational", "big-tech"],
        benefits=["Paid rotational internship", "Exposure to engineering and PM tracks"],
        status="curated",
    ),
    dict(
        title="Outreachy Internships",
        org="Software Freedom Conservancy", org_url="https://sfconservancy.org",
        category="internships", type="internship",
        summary="Paid, remote open-source internships for people subject to under-representation in tech.",
        description=(
            "Outreachy provides paid, fully remote internships working on open-source and open-"
            "science projects. It is aimed at people who face under-representation, systemic bias "
            "or discrimination in the technology industry of their country. The programme runs in "
            "two cohorts a year, each beginning with a contribution period that applicants must "
            "complete before final selection."
        ),
        eligibility="Open to applicants subject to under-representation in tech in their country; see the official eligibility rules.",
        who_can_apply=["Students", "Non-students", "Career changers"],
        location="Remote", remote=True, cost="free",
        url="https://www.outreachy.org/apply/",
        source_url="https://www.outreachy.org/",
        skills=["Open Source", "Git", "Python", "Documentation"],
        tags=["internship", "remote", "open-source", "paid", "diversity"],
        benefits=["Paid remote internship", "Mentorship on a real open-source project"],
        status="curated",
    ),
    dict(
        title="Amazon Software Development Engineer Internship",
        org="Amazon", org_url="https://www.amazon.com",
        category="internships", type="internship",
        summary="Amazon's paid SDE internship for undergraduate and graduate students.",
        description=(
            "Amazon runs paid software development engineering internships for students in "
            "computer science and related degrees, across multiple regions. Interns own a project "
            "with a mentor and manager. Roles are posted on Amazon's student careers site "
            "throughout the year, with hiring timelines varying by country and team."
        ),
        eligibility="Students enrolled in a bachelor's or master's programme in computer science or a related field.",
        who_can_apply=["Undergraduate students", "Master's students"],
        location="Multiple locations", remote=False, cost="free",
        url="https://www.amazon.jobs/en/teams/internships-for-students",
        source_url="https://www.amazon.jobs/en/teams/internships-for-students",
        skills=["Java", "Python", "Distributed Systems", "Algorithms"],
        tags=["internship", "paid", "software-engineering", "big-tech"],
        benefits=["Paid internship with a dedicated project", "Mentorship and manager support"],
        status="needs_review",
    ),
    dict(
        title="Bloomberg Engineering Internship",
        org="Bloomberg", org_url="https://www.bloomberg.com",
        category="internships", type="internship",
        summary="A paid summer software engineering internship at Bloomberg.",
        description=(
            "Bloomberg runs a paid summer internship for software engineering students, based in "
            "its engineering offices including New York and London. Interns join a team and work "
            "on production-facing projects. Applications and locations are listed on Bloomberg's "
            "careers site; timelines differ by region."
        ),
        eligibility="Students in computer science or related degrees; region-specific work authorisation applies.",
        who_can_apply=["Undergraduate students", "Master's students"],
        location="New York, London and other offices", remote=False, cost="free",
        url="https://www.bloomberg.com/company/careers/students/",
        source_url="https://www.bloomberg.com/company/careers/students/",
        skills=["C++", "Python", "JavaScript", "Systems"],
        tags=["internship", "paid", "fintech", "software-engineering"],
        benefits=["Paid summer internship", "Work on production systems"],
        status="needs_review",
    ),
    dict(
        title="Salesforce Futureforce Internship",
        org="Salesforce", org_url="https://www.salesforce.com",
        category="internships", type="internship",
        summary="Salesforce's student programme covering internships across engineering and business.",
        description=(
            "Futureforce is Salesforce's university recruiting programme, covering internships "
            "and early-career roles in software engineering, data, design and business functions. "
            "Roles, locations and application windows are listed on the Salesforce careers site "
            "and vary by region."
        ),
        eligibility="Currently enrolled students; requirements vary by role and region.",
        who_can_apply=["Undergraduate students", "Master's students"],
        location="Multiple locations", remote=False, cost="free",
        url="https://www.salesforce.com/company/careers/university-recruiting/",
        source_url="https://www.salesforce.com/company/careers/university-recruiting/",
        skills=["Software Engineering", "Data", "Cloud", "Java"],
        tags=["internship", "paid", "enterprise", "cloud"],
        benefits=["Paid internship", "Structured university recruiting programme"],
        status="needs_review",
    ),
    dict(
        title="IBM Extreme Blue",
        org="IBM", org_url="https://www.ibm.com",
        category="internships", type="internship",
        summary="IBM's internship pairing technical and business students on a single product project.",
        description=(
            "Extreme Blue is IBM's internship programme in which small teams of technical and "
            "MBA students work together on a product or technology project over a summer, "
            "presenting the result to IBM executives at the end. Availability and locations vary "
            "by year and country."
        ),
        eligibility="Students in technical degrees and MBA students; region-specific requirements apply.",
        who_can_apply=["Technical students", "MBA students"],
        location="Multiple locations", remote=False, cost="free",
        url="https://www.ibm.com/careers/internships",
        source_url="https://www.ibm.com/careers/internships",
        skills=["Software Engineering", "Product Management", "Cloud", "AI"],
        tags=["internship", "paid", "product", "enterprise"],
        benefits=["Team project with executive presentation", "Technical and business mix"],
        status="needs_review",
    ),
]

HACKATHONS = [
    dict(
        title="Major League Hacking Season",
        org="Major League Hacking", org_url="https://mlh.io",
        category="hackathons", type="hackathon",
        summary="MLH's official hackathon league — a continuously updated calendar of student events.",
        description=(
            "Major League Hacking runs the official student hackathon league, listing member "
            "events worldwide across the season. Events are typically free to attend for "
            "students, run over a weekend, and offer mentorship, workshops and prizes. The "
            "calendar is updated continuously, so this entry points at the season listing rather "
            "than a single event."
        ),
        eligibility="Students; individual events may set their own age or enrolment requirements.",
        who_can_apply=["Students", "Recent graduates at some events"],
        location="Global and online", remote=True, cost="free", rolling=True,
        url="https://mlh.io/seasons",
        source_url="https://mlh.io/seasons",
        skills=["Rapid Prototyping", "JavaScript", "Python", "Teamwork"],
        tags=["hackathon", "free", "weekend", "students", "community"],
        benefits=["Free entry to member events", "Mentorship and workshops"],
        status="curated",
    ),
    dict(
        title="NASA Space Apps Challenge",
        org="NASA", org_url="https://www.nasa.gov",
        category="hackathons", type="hackathon",
        summary="A global hackathon using open NASA data, run annually across hundreds of locations.",
        description=(
            "The NASA International Space Apps Challenge is an annual global hackathon in which "
            "teams build solutions to challenges set by NASA, using open space and Earth data. It "
            "runs over one weekend across many local and virtual venues. Participation is free "
            "and open to all ages, with local events organised by community leads."
        ),
        eligibility="Open to everyone; some award categories have age or team requirements.",
        who_can_apply=["Students", "Professionals", "Anyone"],
        location="Global and virtual", remote=True, cost="free",
        url="https://www.spaceappschallenge.org/",
        source_url="https://www.spaceappschallenge.org/",
        skills=["Data Science", "Python", "Visualisation", "Open Data"],
        tags=["hackathon", "space", "open-data", "free", "global"],
        benefits=["Work with open NASA datasets", "Global and local award categories"],
        status="curated",
    ),
    dict(
        title="Smart India Hackathon",
        org="Government of India", org_url="https://www.education.gov.in",
        category="hackathons", type="hackathon",
        summary="A nationwide Indian hackathon where student teams solve problem statements from ministries and industry.",
        description=(
            "Smart India Hackathon is a nationwide initiative in India in which student teams "
            "address problem statements submitted by government ministries, departments and "
            "industry partners. It runs in software and hardware editions with an internal "
            "college-level round preceding the national grand finale. Participation is organised "
            "through students' institutions."
        ),
        eligibility="Students enrolled at participating Indian institutions, entering as a team through their college.",
        who_can_apply=["Indian college students", "Student teams"],
        location="India", remote=False, cost="free",
        url="https://www.sih.gov.in/",
        source_url="https://www.sih.gov.in/",
        skills=["Problem Solving", "Full Stack", "IoT", "AI"],
        tags=["hackathon", "india", "free", "government", "national"],
        benefits=["National-level exposure", "Problem statements from real institutions"],
        status="curated",
    ),
    dict(
        title="ICPC — International Collegiate Programming Contest",
        org="ICPC Foundation", org_url="https://icpc.global",
        category="hackathons", type="competition",
        summary="The long-running team-based algorithmic programming contest for university students.",
        description=(
            "The ICPC is a team-based competitive programming contest for university students, "
            "progressing from regional contests to a World Finals. Teams of three solve "
            "algorithmic problems under time pressure sharing a single machine. Entry is through "
            "a university team and a regional contest; rules on eligibility and years of study "
            "are published by the ICPC Foundation."
        ),
        eligibility="University students meeting ICPC's eligibility rules, competing as a team of three.",
        who_can_apply=["University students", "Teams of three"],
        location="Global regionals", remote=False, cost="free",
        url="https://icpc.global/regionals/",
        source_url="https://icpc.global/",
        skills=["Algorithms", "Data Structures", "C++", "Competitive Programming"],
        tags=["competition", "algorithms", "team", "global"],
        benefits=["Path to the ICPC World Finals", "Recognised by employers in tech"],
        status="curated",
    ),
    dict(
        title="Kaggle Competitions",
        org="Kaggle", org_url="https://www.kaggle.com",
        category="hackathons", type="competition",
        summary="Ongoing machine learning competitions, including beginner-friendly playground contests.",
        description=(
            "Kaggle hosts machine learning competitions ranging from beginner playground "
            "contests to research challenges with prize pools sponsored by companies and "
            "institutions. Competitions run continuously with individual deadlines. Participation "
            "is free; prize eligibility rules vary per competition."
        ),
        eligibility="Open to Kaggle account holders; prize eligibility rules vary by competition.",
        who_can_apply=["Anyone", "Data science students"],
        location="Online", remote=True, cost="free", rolling=True,
        url="https://www.kaggle.com/competitions",
        source_url="https://www.kaggle.com/competitions",
        skills=["Machine Learning", "Python", "Feature Engineering", "Deep Learning"],
        tags=["competition", "ml", "data", "free", "online"],
        benefits=["Public leaderboard results for your portfolio", "Prize pools on sponsored contests"],
        status="curated",
    ),
    dict(
        title="Devpost Hackathon Listings",
        org="Devpost", org_url="https://devpost.com",
        category="hackathons", type="hackathon",
        summary="An aggregated, continuously updated list of open online and in-person hackathons.",
        description=(
            "Devpost hosts and lists hackathons run by companies, communities and universities, "
            "with online events open to participants worldwide. Each listing carries its own "
            "rules, prizes and deadlines. Many events are free to enter and accept student "
            "participants."
        ),
        eligibility="Varies per hackathon; many are open to students worldwide.",
        who_can_apply=["Students", "Developers", "Designers"],
        location="Online and in person", remote=True, cost="free", rolling=True,
        url="https://devpost.com/hackathons",
        source_url="https://devpost.com/hackathons",
        skills=["Rapid Prototyping", "Web Development", "APIs"],
        tags=["hackathon", "online", "free", "prizes"],
        benefits=["Continuously refreshed hackathon list", "Project hosting and judging"],
        status="curated",
    ),
]
# fmt: on


# fmt: off
PROGRAMS = [
    dict(
        title="Google Summer of Code",
        org="Google", org_url="https://www.google.com",
        category="programs", type="program",
        summary="A global, paid programme bringing new contributors into open-source projects.",
        description=(
            "Google Summer of Code pairs new open-source contributors with mentoring "
            "organisations for a funded project over a defined coding period. Contributors "
            "submit a proposal to an accepted organisation; selected contributors receive a "
            "stipend, the amount of which Google sets by country. Since 2022 the programme has "
            "been open to contributors beyond students, subject to the published eligibility "
            "rules."
        ),
        eligibility="Open to new open-source contributors aged 18+ who meet GSoC's published eligibility rules.",
        who_can_apply=["Students", "New open-source contributors"],
        location="Remote", remote=True, cost="free",
        url="https://summerofcode.withgoogle.com/",
        source_url="https://summerofcode.withgoogle.com/",
        skills=["Open Source", "Git", "Python", "C++", "JavaScript"],
        tags=["open-source", "paid", "remote", "mentorship", "fellowship"],
        benefits=["Stipend set by Google", "Mentorship from an open-source organisation"],
        status="curated",
    ),
    dict(
        title="MLH Fellowship",
        org="Major League Hacking", org_url="https://mlh.io",
        category="programs", type="fellowship",
        summary="A remote, project-based software engineering fellowship run in structured cohorts.",
        description=(
            "The MLH Fellowship is a remote programme in which participants work in small pods "
            "on open-source or partner projects with mentorship, following a structured "
            "curriculum over a fixed term. Tracks have included open source, software "
            "engineering and site reliability engineering. Terms, funding arrangements and "
            "available tracks vary by cohort and are published on the official site."
        ),
        eligibility="Students and early-career developers; specific requirements vary by cohort and track.",
        who_can_apply=["Students", "Early-career developers"],
        location="Remote", remote=True, cost="free",
        url="https://fellowship.mlh.io/",
        source_url="https://fellowship.mlh.io/",
        skills=["Open Source", "Software Engineering", "Git", "Code Review"],
        tags=["fellowship", "remote", "open-source", "mentorship"],
        benefits=["Structured remote cohort", "Mentored real-world project work"],
        status="curated",
    ),
    dict(
        title="GitHub Campus Expert",
        org="GitHub", org_url="https://github.com",
        category="programs", type="program",
        summary="GitHub's student leadership programme for building technical communities on campus.",
        description=(
            "GitHub Campus Experts are students trained to build technical communities at their "
            "university. The programme provides training in public speaking, community "
            "leadership, technical writing and event organisation, along with support for running "
            "campus events. Applications open in rounds; requirements are listed on the official "
            "page."
        ),
        eligibility="Students aged 18 or older, enrolled for at least one more year at their institution.",
        who_can_apply=["Undergraduate students", "Community builders"],
        location="Global", remote=True, cost="free",
        url="https://githubcampus.expert/",
        source_url="https://githubcampus.expert/",
        skills=["Community Building", "Public Speaking", "Technical Writing", "Git"],
        tags=["ambassador", "community", "leadership", "free"],
        benefits=["Leadership and communication training", "Support for running campus events"],
        status="curated",
    ),
    dict(
        title="Microsoft Learn Student Ambassadors",
        org="Microsoft", org_url="https://www.microsoft.com",
        category="programs", type="program",
        summary="A global student community programme with tiers, training and Microsoft resources.",
        description=(
            "The Microsoft Learn Student Ambassadors programme is a global community for students "
            "who want to build technical skills and lead activities on campus. Members progress "
            "through tiers by contributing, and get access to training, community events and "
            "Microsoft technical resources. Joining requirements are published on the official "
            "programme page."
        ),
        eligibility="Students aged 16 or older enrolled at an accredited institution.",
        who_can_apply=["Students", "Campus community leaders"],
        location="Global", remote=True, cost="free", rolling=True,
        url="https://mvp.microsoft.com/studentambassadors",
        source_url="https://mvp.microsoft.com/studentambassadors",
        skills=["Community Building", "Azure", "Public Speaking"],
        tags=["ambassador", "community", "azure", "free"],
        benefits=["Technical training and resources", "Global student community"],
        status="curated",
    ),
    dict(
        title="Google Developer Groups on Campus",
        org="Google", org_url="https://developers.google.com",
        category="programs", type="program",
        summary="University chapters running peer learning and events on Google technologies.",
        description=(
            "Google Developer Groups on Campus (formerly Google Developer Student Clubs) are "
            "university-based chapters where students learn Google technologies together through "
            "workshops, study jams and projects. Students can join an existing chapter or apply "
            "to lead one where applications are open for their institution."
        ),
        eligibility="University students; lead applications open in annual rounds per institution.",
        who_can_apply=["University students", "Prospective chapter leads"],
        location="Global", remote=False, cost="free", rolling=True,
        url="https://developers.google.com/community/gdsc",
        source_url="https://developers.google.com/community/gdsc",
        skills=["Android", "Web Development", "Cloud", "Community Building"],
        tags=["community", "campus", "free", "google"],
        benefits=["Peer learning and workshops", "Leadership experience for chapter leads"],
        status="needs_review",
    ),
    dict(
        title="Linux Foundation Mentorship Programme",
        org="The Linux Foundation", org_url="https://www.linuxfoundation.org",
        category="programs", type="fellowship",
        summary="Paid mentorships contributing to open-source projects hosted by the Linux Foundation.",
        description=(
            "LFX Mentorship connects new contributors with mentors on open-source projects hosted "
            "by the Linux Foundation, including cloud-native, networking and security projects. "
            "Mentorships run in terms with a stipend, and each project posts its own requirements "
            "and application window on the LFX platform."
        ),
        eligibility="Open to new open-source contributors; requirements vary per project and term.",
        who_can_apply=["Students", "New open-source contributors"],
        location="Remote", remote=True, cost="free",
        url="https://lfx.linuxfoundation.org/tools/mentorship/",
        source_url="https://lfx.linuxfoundation.org/tools/mentorship/",
        skills=["Open Source", "Go", "Kubernetes", "Linux", "C"],
        tags=["fellowship", "open-source", "remote", "paid", "cloud-native"],
        benefits=["Stipend per mentorship term", "Mentorship on a major open-source project"],
        status="curated",
    ),
    dict(
        title="Kleiner Perkins Fellows Program",
        org="Kleiner Perkins", org_url="https://www.kleinerperkins.com",
        category="programs", type="fellowship",
        summary="A summer fellowship placing engineering, design and product students at startups.",
        description=(
            "The Kleiner Perkins Fellows Program places students in engineering, design and "
            "product roles at technology companies for a summer, alongside a cohort programme of "
            "mentorship and speaker sessions. Applications open annually; requirements and "
            "participating companies are published on the official site."
        ),
        eligibility="Students in engineering, design or product-related degrees; see official criteria.",
        who_can_apply=["Engineering students", "Design students", "Product students"],
        location="United States", remote=False, cost="free",
        url="https://fellows.kleinerperkins.com/",
        source_url="https://fellows.kleinerperkins.com/",
        skills=["Software Engineering", "Product Design", "Product Management"],
        tags=["fellowship", "startup", "summer", "competitive"],
        benefits=["Placement at a technology company", "Cohort mentorship programme"],
        status="needs_review",
    ),
]

SCHOLARSHIPS = [
    dict(
        title="Generation Google Scholarship",
        org="Google", org_url="https://www.google.com",
        category="scholarships", type="scholarship",
        summary="A scholarship for students in computing who are under-represented in technology.",
        description=(
            "The Generation Google Scholarship supports students pursuing computer science "
            "degrees who are historically under-represented in technology. Recipients receive "
            "financial support towards their studies. The programme runs in regional editions "
            "(for example in the Americas, EMEA and Asia Pacific), each with its own eligibility "
            "criteria and application window published by Google."
        ),
        eligibility="Students enrolled in a computer science or related degree who meet the region's published criteria.",
        who_can_apply=["Undergraduate students", "Postgraduate students"],
        location="Regional editions", remote=True, cost="free",
        url="https://buildyourfuture.withgoogle.com/scholarships",
        source_url="https://buildyourfuture.withgoogle.com/scholarships",
        skills=["Computer Science", "Software Engineering"],
        tags=["scholarship", "funding", "diversity", "computer-science"],
        benefits=["Financial support towards study", "Access to a Google scholars community"],
        status="curated",
    ),
    dict(
        title="Google Lime Scholarship",
        org="Google", org_url="https://www.google.com",
        category="scholarships", type="scholarship",
        summary="A scholarship for students with disabilities studying computer science.",
        description=(
            "The Google Lime Scholarship, run with Lime Connect, supports students with "
            "disabilities who are pursuing computer science or a closely related degree. "
            "Recipients receive financial support and access to a scholars' community. "
            "Eligibility and award details are published by Google and Lime Connect each cycle."
        ),
        eligibility="Students with a disability enrolled in a computer science or related degree.",
        who_can_apply=["Students with disabilities", "Computer science students"],
        location="Regional editions", remote=True, cost="free",
        url="https://buildyourfuture.withgoogle.com/scholarships",
        source_url="https://buildyourfuture.withgoogle.com/scholarships",
        skills=["Computer Science", "Software Engineering"],
        tags=["scholarship", "funding", "accessibility", "diversity"],
        benefits=["Financial support towards study", "Scholars' community and events"],
        status="needs_review",
    ),
    dict(
        title="Grace Hopper Celebration Student Scholarship",
        org="AnitaB.org", org_url="https://anitab.org",
        category="scholarships", type="scholarship",
        summary="Sponsored attendance at the Grace Hopper Celebration for students in computing.",
        description=(
            "AnitaB.org awards scholarships for students to attend the Grace Hopper Celebration, "
            "one of the largest gatherings of women and non-binary technologists. Awards "
            "typically cover conference registration and may include travel support, as defined "
            "by AnitaB.org for that year. Applications open annually ahead of the conference."
        ),
        eligibility="Students in computing or related fields; criteria are published by AnitaB.org each year.",
        who_can_apply=["Undergraduate students", "Postgraduate students"],
        location="United States", remote=False, cost="free",
        url="https://ghc.anitab.org/attend/scholarships/",
        source_url="https://ghc.anitab.org/",
        skills=["Computer Science", "Networking"],
        tags=["scholarship", "conference", "diversity", "funding"],
        benefits=["Sponsored conference attendance", "Career fair access"],
        status="curated",
    ),
    dict(
        title="Amazon Future Engineer Scholarship",
        org="Amazon", org_url="https://www.amazon.com",
        category="scholarships", type="scholarship",
        summary="Amazon's scholarship programme for students from under-served communities entering computer science.",
        description=(
            "Amazon Future Engineer provides scholarships and related support for students from "
            "under-served communities pursuing computer science, with programmes running in "
            "several countries. Award values, eligibility and application windows differ by "
            "country and are published on the national Amazon Future Engineer pages."
        ),
        eligibility="Varies by country; generally students from under-served communities entering computer science.",
        who_can_apply=["High school leavers", "Undergraduate students"],
        location="Multiple countries", remote=True, cost="free",
        url="https://www.amazonfutureengineer.com/scholarships",
        source_url="https://www.amazonfutureengineer.com/",
        skills=["Computer Science"],
        tags=["scholarship", "funding", "diversity", "computer-science"],
        benefits=["Scholarship towards a computer science degree", "Programme support resources"],
        status="needs_review",
    ),
    dict(
        title="Adobe Research Women-in-Technology Scholarship",
        org="Adobe", org_url="https://research.adobe.com",
        category="scholarships", type="scholarship",
        summary="Adobe Research's scholarship recognising women in computer science and engineering.",
        description=(
            "The Adobe Research Women-in-Technology Scholarship recognises outstanding women "
            "undergraduates and master's students in computer science, computer engineering and "
            "related fields. Recipients receive an award and, per Adobe's published terms, may be "
            "considered for an internship interview. Criteria and timing are set by Adobe Research "
            "each cycle."
        ),
        eligibility="Women in undergraduate or master's programmes in computing; see Adobe Research's published criteria.",
        who_can_apply=["Undergraduate students", "Master's students"],
        location="Global", remote=True, cost="free",
        url="https://research.adobe.com/scholarship/",
        source_url="https://research.adobe.com/scholarship/",
        skills=["Computer Science", "Research", "Machine Learning"],
        tags=["scholarship", "research", "diversity", "funding"],
        benefits=["Scholarship award", "Consideration for an Adobe internship interview"],
        status="curated",
    ),
    dict(
        title="Reliance Foundation Undergraduate Scholarships",
        org="Reliance Foundation", org_url="https://www.reliancefoundation.org",
        category="scholarships", type="scholarship",
        summary="Merit-and-means scholarships for undergraduate students in India.",
        description=(
            "Reliance Foundation Undergraduate Scholarships support first-year undergraduate "
            "students in India on the basis of merit and financial need, with a grant towards "
            "study. Selection involves an aptitude test and academic criteria. Award value, "
            "eligibility and the application window are published by the Foundation each year."
        ),
        eligibility="First-year undergraduate students in India meeting the published merit and income criteria.",
        who_can_apply=["Indian undergraduate students", "First-year students"],
        location="India", remote=True, cost="free",
        url="https://www.reliancefoundation.org/scholarships",
        source_url="https://www.reliancefoundation.org/scholarships",
        skills=["Academics"],
        tags=["scholarship", "india", "funding", "undergraduate"],
        benefits=["Grant towards undergraduate study", "Access to a scholars' network"],
        status="needs_review",
    ),
    dict(
        title="Quad Fellowship",
        org="Quad Fellowship", org_url="https://www.quadfellowship.org",
        category="scholarships", type="fellowship",
        summary="A graduate STEM fellowship for students from Quad partner countries.",
        description=(
            "The Quad Fellowship supports graduate students in science, technology, engineering "
            "and mathematics from Quad partner countries to study in the United States, combining "
            "financial support with a cohort programme of cross-cultural and professional "
            "activities. Eligibility, award terms and timelines are published on the official "
            "site."
        ),
        eligibility="Graduate STEM students who are citizens or legal permanent residents of participating countries.",
        who_can_apply=["Master's students", "PhD students"],
        location="United States", remote=False, cost="free",
        url="https://www.quadfellowship.org/",
        source_url="https://www.quadfellowship.org/",
        skills=["STEM", "Research"],
        tags=["fellowship", "scholarship", "graduate", "international"],
        benefits=["Financial support for graduate study", "International cohort programme"],
        status="needs_review",
    ),
]

ALL_SEEDS = TECH_BENEFITS + CERTIFICATIONS + INTERNSHIPS + HACKATHONS + PROGRAMS + SCHOLARSHIPS
# fmt: on
