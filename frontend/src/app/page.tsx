import type { Metadata } from "next";
import Link from "next/link";

import { IntroSequence } from "@/components/intro/IntroSequence";
import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { PreviewCard } from "@/components/marketing/PreviewCard";
import { Radar } from "@/components/marketing/Radar";
import { Badge } from "@/components/ui/Badge";
import { ButtonLink } from "@/components/ui/Button";
import {
  IconAward,
  IconBriefcase,
  IconCheck,
  IconGraduationCap,
  IconShield,
  IconSparkles,
  IconTrophy,
  IconUsers,
} from "@/components/ui/Icons";
import { api } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import type { Category, CategoryInfo } from "@/lib/types";

export const metadata: Metadata = {
  title: `${BRAND.wordmark} — ${BRAND.tagline}`,
  description: BRAND.description,
};
export const revalidate = 120;

/**
 * The six categories are a fixed product commitment, so the landing page
 * describes them without needing the API. Live counts are layered on when the
 * catalogue responds, and simply omitted when it does not — which is what
 * happens during a build, before the backend is reachable.
 */
const CATEGORIES: { slug: Category; name: string; description: string }[] = [
  {
    slug: "certifications",
    name: "Certifications",
    description: "Courses, exams and learning platforms that end in a credential.",
  },
  {
    slug: "internships",
    name: "Internships",
    description: "Paid and unpaid roles built for students.",
  },
  {
    slug: "hackathons",
    name: "Hackathons & Competitions",
    description: "Build, compete and win — usually in a weekend.",
  },
  {
    slug: "programs",
    name: "Programs & Fellowships",
    description: "Structured cohorts, ambassadorships and fellowships.",
  },
  {
    slug: "tech_benefits",
    name: "Tech Benefits",
    description: "Free and discounted software, cloud credits and AI tools.",
  },
  {
    slug: "scholarships",
    name: "Scholarships",
    description: "Funding for tuition, travel and research.",
  },
];

const CATEGORY_ICONS: Record<string, typeof IconAward> = {
  certifications: IconAward,
  internships: IconBriefcase,
  hackathons: IconTrophy,
  programs: IconUsers,
  tech_benefits: IconSparkles,
  scholarships: IconGraduationCap,
};

const PIPELINE = [
  {
    step: "Discover",
    body: "Official pages, feeds and APIs are registered as sources, each with a trust level and a check cadence. Sources that disallow automated access are recorded and never fetched.",
  },
  {
    step: "Extract",
    body: "Each fetched document is turned into a structured candidate: what it is, who can apply, what it costs and when it closes.",
  },
  {
    step: "Deduplicate",
    body: "A content fingerprint plus title similarity collapses the same opportunity arriving from several places into one record.",
  },
  {
    step: "Verify",
    body: "Automated checks establish plausibility and produce a confidence score. Low confidence routes to a person — automation never self-approves.",
  },
  {
    step: "Match",
    body: "Your degree, skills, interests and location produce a score with a written reason for every point awarded.",
  },
];

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />
        <nav aria-label="Primary" className="flex items-center gap-1.5 sm:gap-3">
          <Link
            href="#how-it-works"
            className="hidden rounded-lg px-3 py-2 text-[13px] font-medium text-muted transition-colors hover:text-text sm:block"
          >
            How it works
          </Link>
          <Link
            href="/login"
            className="rounded-lg px-3 py-2 text-[13px] font-medium text-muted transition-colors hover:text-text"
          >
            Sign in
          </Link>
          <ThemeToggle />
          <ButtonLink href="/signup" size="sm">
            Get started
          </ButtonLink>
        </nav>
      </div>
    </header>
  );
}

export default async function LandingPage() {
  // Real counts from the catalogue, never invented marketing numbers. If the
  // API is unreachable — during a build, say — the page drops the numbers and
  // keeps everything else.
  const live: CategoryInfo[] = await api.categories().catch(() => []);
  const counts = new Map(live.map((category) => [category.slug, category.count]));
  const total = live.reduce((sum, category) => sum + category.count, 0);

  return (
    <div className="min-h-dvh bg-bg">
      {/*
        Plays once per visitor, on the client only. Returning visitors and
        anyone with prefers-reduced-motion never see it, and it renders nothing
        server-side so the landing page is complete without it.
      */}
      <IntroSequence />
      <Header />

      <main id="main">
        {/* ---------------------------------------------------------------- Hero */}
        <section className="relative overflow-hidden border-b border-border">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:py-24">
            <div>
              <Badge tone="accent" className="mb-5">
                <IconShield />
                Every record carries its official source
              </Badge>

              <h1 className="text-balance text-[38px] font-semibold leading-[1.08] tracking-[-0.03em] text-text sm:text-[52px]">
                Stop searching.
                <br />
                Start discovering.
              </h1>

              <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-muted">
                {BRAND.description}
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <ButtonLink href="/signup" size="lg">
                  Get started
                </ButtonLink>
                <ButtonLink href="/opportunities" size="lg" variant="secondary">
                  Explore opportunities
                </ButtonLink>
              </div>

              {total > 0 ? (
                <p className="tnum mt-6 text-[13px] text-faint">
                  <span className="font-semibold text-text">{total}</span> curated opportunities
                  across {live.filter((c) => c.count > 0).length} categories · browsing is free and
                  needs no account
                </p>
              ) : null}
            </div>

            <div className="relative flex justify-center lg:justify-end lg:pr-6">
              <Radar />

              <PreviewCard
                organization="Example Cloud Provider"
                title="Free cloud certification"
                category="Certification"
                cost="Free"
                deadline="12 days left"
                isNew
                className="absolute -top-2 left-0 hidden scale-[0.82] sm:block lg:-left-20 lg:top-4"
              />
              <PreviewCard
                organization="Example Foundation"
                title="Remote open-source fellowship"
                category="Fellowship"
                cost="Paid"
                deadline="3 days left"
                urgent
                className="absolute -bottom-4 right-0 hidden scale-[0.82] sm:block lg:-right-12"
              />
            </div>
          </div>

          <p className="mx-auto max-w-6xl px-4 pb-6 text-[11.5px] text-faint sm:px-6">
            The two floating cards above are illustrative examples, not live listings. Real records
            are in{" "}
            <Link href="/opportunities" className="text-accent hover:underline">
              the catalogue
            </Link>
            , each labelled with its verification status and source.
          </p>
        </section>

        {/* ---------------------------------------------------------- Categories */}
        <section className="border-b border-border">
            <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
              <h2 className="text-[24px] font-semibold tracking-[-0.02em] text-text">
                Six categories. Nothing else.
              </h2>
              <p className="mt-2 max-w-2xl text-[14.5px] leading-relaxed text-muted">
                Zenkai deliberately does not aggregate general news, random events or generic
                courses. A narrow catalogue is what makes it scannable.
              </p>

              <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {CATEGORIES.map((category) => {
                  const Glyph = CATEGORY_ICONS[category.slug] ?? IconSparkles;
                  const count = counts.get(category.slug);
                  return (
                    <Link
                      key={category.slug}
                      href={`/opportunities?category=${category.slug}`}
                      className="group rounded-panel border border-border bg-surface p-5 transition-[border-color,box-shadow,transform] hover:-translate-y-px hover:border-border-strong hover:shadow-float"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <span className="grid size-9 place-items-center rounded-[10px] bg-bg-subtle text-[17px] text-accent">
                          <Glyph />
                        </span>
                        {count !== undefined ? (
                          <span className="tnum text-[12.5px] font-medium text-faint">{count}</span>
                        ) : null}
                      </div>
                      <h3 className="mt-3.5 text-[14.5px] font-semibold text-text group-hover:text-accent">
                        {category.name}
                      </h3>
                      <p className="mt-1 text-[12.5px] leading-relaxed text-muted">
                        {category.description}
                      </p>
                    </Link>
                  );
                })}
              </div>
            </div>
          </section>

        {/* -------------------------------------------------------- How it works */}
        <section id="how-it-works" className="scroll-mt-20 border-b border-border">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
            <h2 className="text-[24px] font-semibold tracking-[-0.02em] text-text">
              How an opportunity reaches you
            </h2>
            <p className="mt-2 max-w-2xl text-[14.5px] leading-relaxed text-muted">
              Five stages, each one auditable. The pipeline is built; automated fetching is the
              piece still to come, which is why today&apos;s catalogue is curated by hand and
              labelled as such on every record.
            </p>

            <ol className="mt-8 grid gap-px overflow-hidden rounded-panel border border-border bg-border sm:grid-cols-2 lg:grid-cols-5">
              {PIPELINE.map((stage, index) => (
                <li key={stage.step} className="bg-surface p-5">
                  <span className="tnum text-[11px] font-semibold text-faint">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h3 className="mt-1.5 text-[14px] font-semibold text-text">{stage.step}</h3>
                  <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{stage.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ---------------------------------------------------------- Honest bit */}
        <section className="border-b border-border">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-2">
            <div>
              <h2 className="text-[24px] font-semibold tracking-[-0.02em] text-text">
                What Zenkai does not claim
              </h2>
              <p className="mt-2 text-[14.5px] leading-relaxed text-muted">
                Opportunity aggregators tend to overstate their coverage and their confidence. These
                are the limits of this build, stated plainly.
              </p>
            </div>

            <ul className="space-y-3.5">
              {[
                "It does not scan the whole internet. Today's catalogue is curated by hand from official pages, and every record says so.",
                "“Curated” means a person wrote the record from the official page. Nothing re-checks it afterwards, so details can have moved on.",
                "Deadlines and costs appear only where the official source publishes them. Where it does not, Zenkai says “not listed” rather than guessing.",
                "Match scores are fixed rules with visible reasons, not machine learning, and not a prediction of acceptance.",
                "Sources that prohibit automated access are recorded and never fetched.",
              ].map((line) => (
                <li key={line} className="flex items-start gap-2.5">
                  <IconCheck className="mt-[3px] text-[14px] text-verified" />
                  <span className="text-[13.5px] leading-relaxed text-muted">{line}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ---------------------------------------------------------------- CTA */}
        <section className="mx-auto max-w-6xl px-4 py-20 text-center sm:px-6">
          <h2 className="text-balance text-[28px] font-semibold tracking-[-0.02em] text-text sm:text-[34px]">
            Your opportunity radar.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-[15px] leading-relaxed text-muted">
            Set your degree, skills and interests once. Zenkai ranks every opportunity against them
            and shows you why each one surfaced.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/signup" size="lg">
              Create your account
            </ButtonLink>
            <ButtonLink href="/opportunities" size="lg" variant="secondary">
              Browse without an account
            </ButtonLink>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 sm:px-6">
          <Logo />
          <p className="max-w-md text-[12px] leading-relaxed text-faint">
            {BRAND.tagline} An opportunity intelligence platform for students. Always confirm
            details on the official source before applying.
          </p>
        </div>
      </footer>
    </div>
  );
}
