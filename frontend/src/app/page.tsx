import type { Metadata } from "next";
import Link from "next/link";

import { IntroSequence } from "@/components/intro/IntroSequence";
import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Radar } from "@/components/marketing/Radar";
import { ButtonLink } from "@/components/ui/Button";
import {
  IconArrowRight,
  IconAward,
  IconBolt,
  IconBriefcase,
  IconCheck,
  IconClock,
  IconGraduationCap,
  IconRadar,
  IconSearch,
  IconShield,
  IconSparkles,
  IconTrophy,
  IconUsers,
} from "@/components/ui/Icons";
import { api } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { CATEGORY_SHORT, cx, deadlineLabel, urgencyOf } from "@/lib/format";
import type { Category, CategoryInfo, Opportunity } from "@/lib/types";

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
    slug: "internships",
    name: "Internships",
    description: "Paid and unpaid roles for students, linked to the employer's own application page.",
  },
  {
    slug: "hackathons",
    name: "Hackathons & Competitions",
    description: "Online and in-person events, with the real registration deadline.",
  },
  {
    slug: "certifications",
    name: "Certifications",
    description: "Courses, exams and learning paths that end in a credential.",
  },
  {
    slug: "tech_benefits",
    name: "Tech Benefits",
    description: "Free software, cloud credits and tools for verified students.",
  },
  {
    slug: "programs",
    name: "Programs & Fellowships",
    description: "Structured cohorts, ambassadorships and fellowships.",
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

/** Where the catalogue is read from. Kept in step with app/seed/sources.py. */
const SOURCES = [
  "Devpost",
  "Major League Hacking",
  "Unstop",
  "SimplifyJobs",
  "Microsoft Learn",
  "GitHub Student Pack",
  "Outreachy",
  "Google Developers",
  "Opportunity Desk",
];

const STEPS = [
  {
    icon: IconRadar,
    title: "Fetched from the source",
    body: "Official APIs, feeds and pages are read every six hours. Sites that disallow automated access are never fetched.",
  },
  {
    icon: IconShield,
    title: "Checked and de-duplicated",
    body: "The same opportunity seen in several places becomes one record. Closed or withdrawn listings drop off on their own.",
  },
  {
    icon: IconSparkles,
    title: "Ranked for you",
    body: "Your degree, skills and interests produce a match score, with a written reason for every point.",
  },
];

const URGENCY_TONE: Record<string, string> = {
  today: "bg-critical-soft text-critical",
  critical: "bg-critical-soft text-critical",
  soon: "bg-soon-soft text-soon",
  upcoming: "bg-calm-soft text-calm",
  rolling: "bg-calm-soft text-calm",
  closed: "bg-calm-soft text-calm",
};

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />
        <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/opportunities"
            className="hidden rounded-lg px-3 py-2 text-[13px] font-medium text-muted transition-colors hover:text-text md:block"
          >
            Explore
          </Link>
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

/** A real listing, closest deadline first — not a mock-up. */
function FeedRow({ opportunity }: { opportunity: Opportunity }) {
  const urgency = urgencyOf(opportunity.days_left, opportunity.is_rolling);
  return (
    <li>
      <Link
        href={`/opportunities/${opportunity.slug}`}
        className="group flex items-center gap-3 rounded-[10px] px-3 py-2.5 transition-colors hover:bg-bg-subtle"
      >
        <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-bg-subtle text-[15px] text-accent group-hover:bg-surface">
          {(() => {
            const Glyph = CATEGORY_ICONS[opportunity.category] ?? IconSparkles;
            return <Glyph />;
          })()}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] font-medium text-text group-hover:text-accent">
            {opportunity.title}
          </span>
          <span className="block truncate text-[11.5px] text-faint">
            {opportunity.organization.name} · {CATEGORY_SHORT[opportunity.category]}
          </span>
        </span>
        <span
          className={cx(
            "tnum shrink-0 rounded-md px-1.5 py-0.5 text-[11px] font-semibold",
            URGENCY_TONE[urgency],
          )}
        >
          {deadlineLabel(opportunity)}
        </span>
      </Link>
    </li>
  );
}

function LivePanel({ items }: { items: Opportunity[] }) {
  return (
    <div className="relative w-full max-w-md rounded-[18px] border border-border bg-surface/90 p-2 shadow-[0_24px_64px_-24px_rgb(0_0_0/0.45)] backdrop-blur">
      <div className="flex items-center justify-between px-3 pb-2 pt-2.5">
        <p className="flex items-center gap-2 text-[12px] font-semibold text-text">
          <IconClock className="text-[14px] text-accent" />
          Closing soon
        </p>
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-verified">
          <span className="relative flex size-1.5">
            <span className="absolute inline-flex size-full rounded-full bg-verified opacity-60 motion-safe:animate-ping" />
            <span className="relative inline-flex size-1.5 rounded-full bg-verified" />
          </span>
          Live
        </span>
      </div>
      <ul className="space-y-0.5">
        {items.map((item) => (
          <FeedRow key={item.id} opportunity={item} />
        ))}
      </ul>
      <Link
        href="/opportunities?sort=deadline"
        className="mt-1 flex items-center justify-center gap-1.5 rounded-[10px] border-t border-border px-3 py-2.5 text-[12px] font-medium text-muted transition-colors hover:text-accent"
      >
        See every deadline <IconArrowRight className="text-[13px]" />
      </Link>
    </div>
  );
}

export default async function LandingPage() {
  // Real counts and real listings, never invented marketing numbers. If the
  // API is unreachable — during a build, say — the page drops them and keeps
  // everything else.
  const [live, feed] = await Promise.all([
    api.categories().catch((): CategoryInfo[] => []),
    api
      .publicFeed({ sort: "deadline", limit: 100, deadline_within_days: 30 })
      .then((page) => page.items)
      .catch((): Opportunity[] => []),
  ]);
  const counts = new Map(live.map((category) => [category.slug, category.count]));
  const total = live.reduce((sum, category) => sum + category.count, 0);

  // One per category where possible, so the panel shows the range of the
  // catalogue rather than six hackathons closing on the same day.
  const closing: Opportunity[] = [];
  const seen = new Set<string>();
  for (const item of feed) {
    if ((item.days_left ?? -1) < 0 || seen.has(item.category)) continue;
    seen.add(item.category);
    closing.push(item);
  }
  for (const item of feed) {
    if (closing.length >= 5) break;
    if ((item.days_left ?? -1) >= 0 && !closing.includes(item)) closing.push(item);
  }
  const shown = closing.slice(0, 5);

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
          {/* Backdrop: a soft accent glow over a faint grid, fading out. */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,black,transparent)]"
            style={{
              backgroundImage:
                "linear-gradient(to right, var(--border) 1px, transparent 1px), linear-gradient(to bottom, var(--border) 1px, transparent 1px)",
              backgroundSize: "44px 44px",
              opacity: 0.55,
            }}
          />
          <div
            aria-hidden
            className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-accent opacity-[0.12] blur-[120px]"
          />

          <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pb-24 lg:pt-20">
            <div>
              <Link
                href="/opportunities?sort=newest"
                className="group mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-surface/70 py-1 pl-1.5 pr-3 text-[12px] text-muted backdrop-blur transition-colors hover:border-border-strong hover:text-text"
              >
                <span className="flex items-center gap-1.5 rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-semibold text-accent">
                  <IconBolt className="text-[11px]" />
                  Live
                </span>
                Refreshed from the source every six hours
                <IconArrowRight className="text-[12px] transition-transform group-hover:translate-x-0.5" />
              </Link>

              <h1 className="text-balance text-[42px] font-semibold leading-[1.04] tracking-[-0.035em] text-text sm:text-[60px]">
                Stop searching.
                <br />
                <span className="bg-linear-to-r from-accent to-accent-hover bg-clip-text text-transparent">
                  Start discovering.
                </span>
              </h1>

              <p className="mt-5 max-w-xl text-[16.5px] leading-relaxed text-muted">
                Internships, hackathons, certifications, scholarships, programs and student
                benefits — gathered from official sources into one place, ranked for you, with
                the real deadline on every one.
              </p>

              {/* A real search, straight into the catalogue. */}
              <form
                action="/opportunities"
                method="get"
                role="search"
                className="mt-8 flex max-w-xl items-center gap-2 rounded-[14px] border border-border bg-surface p-1.5 shadow-float transition-[border-color,box-shadow] focus-within:border-accent focus-within:ring-4 focus-within:ring-accent-ring"
              >
                <IconSearch className="ml-2.5 shrink-0 text-[17px] text-faint" />
                <label htmlFor="landing-search" className="sr-only">
                  Search opportunities
                </label>
                <input
                  id="landing-search"
                  name="q"
                  type="search"
                  placeholder="Try “AI hackathon”, “Azure”, “remote internship”"
                  className="min-w-0 flex-1 bg-transparent py-2 text-[14.5px] text-text placeholder:text-faint focus:outline-none"
                />
                <button
                  type="submit"
                  className="shrink-0 rounded-[10px] bg-accent px-4 py-2 text-[13.5px] font-semibold text-white transition-colors hover:bg-accent-hover"
                >
                  Search
                </button>
              </form>

              <div className="mt-4 flex flex-wrap gap-2">
                {CATEGORIES.map((category) => (
                  <Link
                    key={category.slug}
                    href={`/opportunities?category=${category.slug}`}
                    className="rounded-full border border-border bg-surface/60 px-3 py-1 text-[12px] font-medium text-muted transition-colors hover:border-accent hover:text-accent"
                  >
                    {CATEGORY_SHORT[category.slug]}
                  </Link>
                ))}
              </div>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <ButtonLink href="/signup" size="lg">
                  Get started — it&apos;s free
                </ButtonLink>
                <ButtonLink href="/opportunities" size="lg" variant="secondary">
                  Browse without an account
                </ButtonLink>
              </div>
            </div>

            <div className="relative flex min-h-[340px] items-center justify-center lg:justify-end">
              <Radar className="absolute opacity-40 lg:-right-10" />
              {shown.length > 0 ? <LivePanel items={shown} /> : <Radar />}
            </div>
          </div>

          {/* Live numbers, straight from the catalogue. */}
          {total > 0 ? (
            <div className="relative border-t border-border bg-surface/40">
              <dl className="mx-auto grid max-w-6xl grid-cols-2 divide-border px-4 sm:px-6 md:grid-cols-4 md:divide-x">
                {[
                  { value: total.toLocaleString("en-IN"), label: "open opportunities" },
                  {
                    value: String(live.filter((c) => c.count > 0).length),
                    label: "categories",
                  },
                  { value: String(SOURCES.length), label: "live sources" },
                  { value: "6h", label: "refresh cycle" },
                ].map((stat) => (
                  <div key={stat.label} className="py-5 md:px-6 md:first:pl-0">
                    <dt className="text-[12px] text-faint">{stat.label}</dt>
                    <dd className="tnum mt-0.5 text-[24px] font-semibold tracking-[-0.02em] text-text">
                      {stat.value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}
        </section>

        {/* ------------------------------------------------------------- Sources */}
        <section className="border-b border-border">
          <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 sm:px-6 md:flex-row md:items-center">
            <p className="shrink-0 text-[12px] font-medium uppercase tracking-[0.08em] text-faint">
              Pulled live from
            </p>
            <ul className="flex flex-wrap gap-x-6 gap-y-2">
              {SOURCES.map((source) => (
                <li key={source} className="text-[14px] font-semibold tracking-[-0.01em] text-muted">
                  {source}
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ---------------------------------------------------------- Categories */}
        <section className="border-b border-border">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-accent">
                  Six categories
                </p>
                <h2 className="mt-2 text-[30px] font-semibold tracking-[-0.025em] text-text">
                  Everything a student can apply for.
                </h2>
                <p className="mt-2 max-w-xl text-[14.5px] leading-relaxed text-muted">
                  No news, no random events, no generic courses. A narrow catalogue is what makes
                  it worth scanning.
                </p>
              </div>
              <Link
                href="/opportunities"
                className="flex items-center gap-1.5 text-[13px] font-medium text-accent hover:underline"
              >
                Browse all <IconArrowRight className="text-[13px]" />
              </Link>
            </div>

            <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {CATEGORIES.map((category) => {
                const Glyph = CATEGORY_ICONS[category.slug] ?? IconSparkles;
                const count = counts.get(category.slug);
                return (
                  <Link
                    key={category.slug}
                    href={`/opportunities?category=${category.slug}`}
                    className="group relative overflow-hidden rounded-[16px] border border-border bg-surface p-6 transition-[border-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-accent/50 hover:shadow-float"
                  >
                    <div
                      aria-hidden
                      className="pointer-events-none absolute -right-10 -top-10 size-36 rounded-full bg-accent opacity-0 blur-3xl transition-opacity group-hover:opacity-[0.12]"
                    />
                    <div className="flex items-start justify-between gap-3">
                      <span className="grid size-10 place-items-center rounded-[12px] bg-accent-soft text-[18px] text-accent">
                        <Glyph />
                      </span>
                      <IconArrowRight className="text-[15px] text-faint transition-[transform,color] group-hover:translate-x-0.5 group-hover:text-accent" />
                    </div>
                    {count !== undefined ? (
                      <p className="tnum mt-6 text-[32px] font-semibold leading-none tracking-[-0.03em] text-text">
                        {count.toLocaleString("en-IN")}
                      </p>
                    ) : null}
                    <h3 className={cx("text-[15px] font-semibold text-text", count !== undefined ? "mt-2" : "mt-6")}>
                      {category.name}
                    </h3>
                    <p className="mt-1 text-[13px] leading-relaxed text-muted">
                      {category.description}
                    </p>
                  </Link>
                );
              })}
            </div>
          </div>
        </section>

        {/* -------------------------------------------------------- How it works */}
        <section id="how-it-works" className="scroll-mt-20 border-b border-border bg-bg-subtle/50">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-accent">
              How it works
            </p>
            <h2 className="mt-2 text-[30px] font-semibold tracking-[-0.025em] text-text">
              From the source to your shortlist.
            </h2>

            <ol className="mt-10 grid gap-4 md:grid-cols-3">
              {STEPS.map((step, index) => (
                <li
                  key={step.title}
                  className="relative rounded-[16px] border border-border bg-surface p-6"
                >
                  <div className="flex items-center justify-between">
                    <span className="grid size-10 place-items-center rounded-[12px] bg-accent-soft text-[18px] text-accent">
                      <step.icon />
                    </span>
                    <span className="tnum text-[40px] font-semibold leading-none tracking-[-0.04em] text-border-strong">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="mt-5 text-[15.5px] font-semibold text-text">{step.title}</h3>
                  <p className="mt-1.5 text-[13.5px] leading-relaxed text-muted">{step.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* ---------------------------------------------------------- Honest bit */}
        <section className="border-b border-border">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[1fr_1.2fr]">
            <div>
              <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-accent">
                Straight answers
              </p>
              <h2 className="mt-2 text-[30px] font-semibold tracking-[-0.025em] text-text">
                What Zenkai does not claim.
              </h2>
              <p className="mt-3 text-[14.5px] leading-relaxed text-muted">
                Aggregators tend to overstate their coverage and their confidence. These are the
                limits, stated plainly.
              </p>
            </div>

            <ul className="grid gap-3 sm:grid-cols-2">
              {[
                "Every record links to its source. Always confirm details there before applying.",
                "Listings found automatically say “Needs verification” until a person reviews them.",
                "Deadlines and costs appear only where the source publishes them — never guessed.",
                "Match scores are fixed rules with visible reasons, not a prediction of acceptance.",
                "Sites that prohibit automated access are never fetched.",
                "It does not scan the whole internet — only the sources listed above.",
              ].map((line) => (
                <li
                  key={line}
                  className="flex items-start gap-2.5 rounded-[12px] border border-border bg-surface p-4"
                >
                  <IconCheck className="mt-[3px] shrink-0 text-[14px] text-verified" />
                  <span className="text-[13px] leading-relaxed text-muted">{line}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ---------------------------------------------------------------- CTA */}
        <section className="px-4 py-20 sm:px-6">
          <div className="relative mx-auto max-w-5xl overflow-hidden rounded-[24px] border border-border bg-surface px-6 py-14 text-center sm:px-12">
            <div
              aria-hidden
              className="pointer-events-none absolute -bottom-32 left-1/2 h-72 w-[640px] -translate-x-1/2 rounded-full bg-accent opacity-[0.18] blur-[100px]"
            />
            <h2 className="relative text-balance text-[30px] font-semibold tracking-[-0.025em] text-text sm:text-[38px]">
              Your opportunity radar.
            </h2>
            <p className="relative mx-auto mt-3 max-w-xl text-[15px] leading-relaxed text-muted">
              Set your degree, skills and interests once. Zenkai ranks every opportunity against
              them, tracks your deadlines, and shows you why each one surfaced.
            </p>
            <div className="relative mt-8 flex flex-wrap justify-center gap-3">
              <ButtonLink href="/signup" size="lg">
                Create your free account
              </ButtonLink>
              <ButtonLink href="/opportunities" size="lg" variant="secondary">
                Explore opportunities
              </ButtonLink>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-8 sm:px-6">
          <Logo />
          <nav aria-label="Footer" className="flex flex-wrap gap-5 text-[12.5px] text-muted">
            <Link href="/opportunities" className="hover:text-text">
              Opportunities
            </Link>
            <Link href="#how-it-works" className="hover:text-text">
              How it works
            </Link>
            <Link href="/login" className="hover:text-text">
              Sign in
            </Link>
          </nav>
          <p className="w-full text-[12px] leading-relaxed text-faint md:w-auto md:max-w-sm">
            {BRAND.tagline} Always confirm details on the official source before applying.
          </p>
        </div>
      </footer>
    </div>
  );
}
