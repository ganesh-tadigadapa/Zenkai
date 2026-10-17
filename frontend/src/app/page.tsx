import type { Metadata } from "next";
import { Instrument_Serif } from "next/font/google";
import Link from "next/link";
import type { CSSProperties } from "react";

import { GuestButton } from "@/components/auth/GuestButton";
import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Spotlight } from "@/components/marketing/Spotlight";
import { ButtonLink } from "@/components/ui/Button";
import {
  IconArrowRight,
  IconAward,
  IconBriefcase,
  IconCheck,
  IconClock,
  IconGraduationCap,
  IconShield,
  IconSparkles,
  IconTrophy,
  IconUsers,
} from "@/components/ui/Icons";
import { BRAND } from "@/lib/brand";

const serif = Instrument_Serif({
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: `${BRAND.wordmark} — ${BRAND.tagline}`,
  description: BRAND.description,
};

/** Cycled in the headline: "Stop searching for …". */
const ROTATING = [
  "internships.",
  "hackathons.",
  "certifications.",
  "scholarships.",
  "fellowships.",
  "student perks.",
];

/** Where records come from, as named in the source registry. */
const SOURCES = [
  "Devpost",
  "Major League Hacking",
  "Unstop",
  "GitHub Education",
  "Microsoft Learn",
  "Google Summer of Code",
  "Outreachy",
  "SimplifyJobs",
  "AWS",
  "Microsoft Azure",
];

const CATEGORIES = [
  { name: "Internships", icon: IconBriefcase },
  { name: "Hackathons", icon: IconTrophy },
  { name: "Certifications", icon: IconAward },
  { name: "Scholarships", icon: IconGraduationCap },
  { name: "Fellowships", icon: IconUsers },
  { name: "Tech benefits", icon: IconSparkles },
];

/** Entrance delay for an `.animate-blur-in` element, or any `--d` consumer. */
const delay = (ms: number) => ({ "--d": `${ms}ms` }) as CSSProperties;
const vars = (values: Record<string, string | number>) => values as CSSProperties;

function Header() {
  return (
    <header className="fixed inset-x-0 top-3 z-40 px-3 sm:top-4">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-4 rounded-full border border-border/80 bg-surface/60 pl-4 pr-2 shadow-[var(--shadow-md)] backdrop-blur-xl sm:pl-5">
        <Logo />
        <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/opportunities"
            className="hidden px-3 py-2 text-[13px] text-muted transition-colors hover:text-text sm:block"
          >
            Browse
          </Link>
          <Link
            href="/login"
            className="px-3 py-2 text-[13px] text-muted transition-colors hover:text-text"
          >
            Sign in
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}

/** The one call to action, with a light travelling round its edge. */
function PrimaryCta({ children }: { children: React.ReactNode }) {
  return (
    <span className="glow-border isolate">
      <GuestButton variant="ink" className="rounded-full px-8">
        {children}
      </GuestButton>
    </span>
  );
}

/** The closing call to action: same glow, but leads into the catalogue. */
function BrowseCta() {
  return (
    <span className="glow-border isolate">
      <ButtonLink href="/opportunities" variant="ink" size="lg" className="group rounded-full px-8">
        Browse opportunities
        <IconArrowRight className="transition-transform group-hover:translate-x-0.5" />
      </ButtonLink>
    </span>
  );
}

function Marquee({
  children,
  reverse = false,
  speed = "40s",
}: {
  children: React.ReactNode[];
  reverse?: boolean;
  speed?: string;
}) {
  return (
    <div
      className="overflow-hidden"
      style={{
        maskImage: "linear-gradient(to right, transparent, black 12%, black 88%, transparent)",
      }}
    >
      {/* Two copies, so the loop is seamless at -50%. The second is hidden from screen readers. */}
      <div
        className={`${reverse ? "animate-marquee-reverse" : "animate-marquee"} flex w-max hover:[animation-play-state:paused]`}
        style={vars({ "--speed": speed })}
      >
        <ul className="flex shrink-0 items-center gap-4 pr-4">{children}</ul>
        <ul aria-hidden className="flex shrink-0 items-center gap-4 pr-4">
          {children}
        </ul>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------- Feature cards */

function SourcesVisual() {
  return (
    <div className="relative grid h-full place-items-center">
      {[0, 1200, 2400].map((ms) => (
        <span
          key={ms}
          className="hero-ring !w-[220px] !border-accent/40"
          style={{ ...delay(ms), animationDuration: "3.6s" }}
        />
      ))}
      <span className="relative grid size-14 place-items-center rounded-2xl border border-border-strong bg-surface text-[22px] text-accent shadow-[var(--shadow-md)]">
        <IconShield />
      </span>
      <span
        className="animate-float absolute left-[14%] top-[22%] rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] text-muted shadow-[var(--shadow-sm)]"
        style={delay(0)}
      >
        devpost.com
      </span>
      <span
        className="animate-float absolute bottom-[18%] right-[10%] inline-flex items-center gap-1 rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] text-muted shadow-[var(--shadow-sm)]"
        style={delay(1500)}
      >
        <IconCheck className="text-verified" />
        Official page
      </span>
    </div>
  );
}

function MatchVisual() {
  const bars = [
    { label: "Category", w: 1 },
    { label: "Interests", w: 0.85 },
    { label: "Skills", w: 0.65 },
    { label: "Location", w: 0.9 },
  ];
  return (
    <div className="flex h-full flex-col justify-center gap-3.5 px-2">
      {bars.map((bar, index) => (
        <div key={bar.label} className="grid grid-cols-[72px_1fr] items-center gap-3">
          <span className="text-[11.5px] text-faint">{bar.label}</span>
          <span className="h-2 overflow-hidden rounded-full bg-bg-subtle">
            <span
              className="bar-fill block h-full rounded-full bg-gradient-to-r from-accent/60 to-accent"
              style={vars({ "--w": bar.w, "--d": `${index * 180}ms` })}
            />
          </span>
        </div>
      ))}
    </div>
  );
}

function DeadlineVisual() {
  return (
    <div className="relative grid h-full place-items-center">
      <svg viewBox="0 0 120 120" className="size-32 -rotate-90" aria-hidden>
        <circle cx="60" cy="60" r="48" fill="none" stroke="var(--border)" strokeWidth="6" />
        <circle
          className="dial"
          cx="60"
          cy="60"
          r="48"
          fill="none"
          stroke="var(--accent)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray="90 211.6"
        />
      </svg>
      <span className="absolute grid place-items-center text-[24px] text-text">
        <IconClock />
      </span>
      <span
        className="animate-float absolute right-[8%] top-[20%] rounded-full border border-critical/30 bg-critical-soft px-2.5 py-1 text-[11px] font-medium text-critical"
        style={delay(800)}
      >
        Closes soon
      </span>
    </div>
  );
}

const FEATURES = [
  {
    title: "Official sources only",
    body: "Every listing links back to the page it came from.",
    visual: SourcesVisual,
  },
  {
    title: "Ranked for you",
    body: "Tell it what you study and love. It sorts the rest, and shows why.",
    visual: MatchVisual,
  },
  {
    title: "Never miss a deadline",
    body: "Save what matters and see what closes next.",
    visual: DeadlineVisual,
  },
];

export default function LandingPage() {
  return (
    <div className={`${serif.variable} min-h-dvh overflow-x-clip bg-bg`}>
      <Header />

      <main id="main">
        {/* ---------------------------------------------------------------- Hero */}
        <Spotlight className="overflow-hidden" size={520} strength={10}>
          <section className="relative flex min-h-dvh items-center justify-center px-4 sm:px-6">
            <div aria-hidden className="animate-blur-in pointer-events-none absolute inset-0">
              <div className="hero-glow" />
              {[0, 3000, 6000].map((ms) => (
                <span key={ms} className="hero-ring" style={delay(ms)} />
              ))}
            </div>
            <div aria-hidden className="grain pointer-events-none absolute inset-0" />
            {/* Fades the glow and rings out, so the hero has no hard bottom edge. */}
            <div
              aria-hidden
              className="pointer-events-none absolute inset-x-0 bottom-0 h-56 bg-gradient-to-b from-transparent to-bg"
            />

            <div className="relative mx-auto max-w-4xl text-center">
              <p
                className="animate-blur-in inline-flex items-center gap-2 rounded-full border border-border bg-surface/60 px-3.5 py-1.5 text-[12.5px] text-muted backdrop-blur"
                style={delay(0)}
              >
                <span className="relative flex size-1.5">
                  <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-70 motion-reduce:hidden" />
                  <span className="relative inline-flex size-1.5 rounded-full bg-accent" />
                </span>
                {BRAND.tagline}
              </p>

              <h1 className="mt-7 text-[40px] font-semibold leading-[1.05] tracking-[-0.045em] text-text sm:text-[64px]">
                <span className="animate-blur-in inline-block" style={delay(120)}>
                  Stop searching for
                </span>
                <br />
                <span
                  className="animate-blur-in font-accent inline-block text-[50px] leading-[1.05] sm:text-[80px]"
                  style={delay(280)}
                >
                  <span className="word-cycle">
                    {ROTATING.map((word, index) => (
                      <span
                        key={word}
                        aria-hidden={index > 0}
                        className="bg-gradient-to-r from-accent via-[color-mix(in_srgb,var(--accent)_70%,var(--text))] to-[color-mix(in_srgb,var(--accent)_35%,var(--text))] bg-clip-text px-2 pb-2 text-transparent"
                        style={vars({ "--i": index })}
                      >
                        {word}
                      </span>
                    ))}
                  </span>
                </span>
              </h1>

              <p
                className="animate-blur-in mx-auto mt-5 max-w-md text-pretty text-[16px] leading-relaxed text-muted sm:text-[17px]"
                style={delay(420)}
              >
                Every opportunity worth your time, gathered from official sources and ranked for
                you.
              </p>

              <div className="animate-blur-in mt-10" style={delay(540)}>
                <PrimaryCta>Get started — it&apos;s free</PrimaryCta>
              </div>
              <p className="animate-blur-in mt-4 text-[12.5px] text-faint" style={delay(620)}>
                No sign-up needed
              </p>
            </div>
          </section>
        </Spotlight>

        {/* ------------------------------------------------------------ Marquees */}
        <section aria-label="Sources and categories" className="space-y-5 pb-24">
          <p className="reveal-on-scroll pb-3 text-center text-[12.5px] text-faint">
            Gathered from official sources
          </p>
          <Marquee speed="45s">
            {SOURCES.map((name) => (
              <li
                key={name}
                className="flex items-center gap-8 whitespace-nowrap pl-4 text-[17px] font-semibold tracking-[-0.01em] text-faint"
              >
                {name}
                <span aria-hidden className="size-1 rounded-full bg-border-strong" />
              </li>
            ))}
          </Marquee>
          <Marquee reverse speed="38s">
            {CATEGORIES.map(({ name, icon: Glyph }) => (
              <li
                key={name}
                className="inline-flex items-center gap-2 whitespace-nowrap rounded-full border border-border bg-surface px-4 py-2 text-[13.5px] text-muted"
              >
                <Glyph className="text-accent" />
                {name}
              </li>
            ))}
          </Marquee>
        </section>

        {/* ------------------------------------------------------------ Features */}
        <section className="px-4 pb-28 pt-8 sm:px-6">
          <div className="reveal-on-scroll mx-auto max-w-xl text-center">
            <h2 className="text-balance text-[30px] font-semibold leading-[1.1] tracking-[-0.035em] text-text sm:text-[40px]">
              Built to save you <span className="font-accent text-[1.12em]">time.</span>
            </h2>
          </div>

          <ul className="mx-auto mt-14 grid max-w-5xl gap-4 md:grid-cols-3">
            {FEATURES.map(({ title, body, visual: Visual }) => (
              <li key={title} className="reveal-on-scroll">
                <Spotlight className="h-full overflow-hidden rounded-3xl border border-border bg-surface shadow-[inset_0_1px_0_0_color-mix(in_srgb,var(--text)_7%,transparent)] transition-[border-color,transform] duration-300 hover:-translate-y-1 hover:border-border-strong">
                  <div className="relative h-52 overflow-hidden border-b border-border bg-[radial-gradient(ellipse_at_50%_0%,color-mix(in_srgb,var(--accent)_7%,transparent),transparent_70%)]">
                    <Visual />
                  </div>
                  <div className="relative p-6">
                    <h3 className="text-[16px] font-medium text-text">{title}</h3>
                    <p className="mt-1.5 text-[14px] leading-relaxed text-muted">{body}</p>
                  </div>
                </Spotlight>
              </li>
            ))}
          </ul>
        </section>

        {/* ---------------------------------------------------------------- CTA */}
        <section className="relative overflow-hidden border-t border-border px-4 py-28 text-center sm:px-6 sm:py-36">
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div className="hero-glow opacity-60" style={{ top: "100%" }} />
          </div>
          <div className="reveal-on-scroll relative">
            <h2 className="text-balance text-[32px] font-semibold leading-[1.08] tracking-[-0.04em] text-text sm:text-[52px]">
              Your next opportunity
              <br />
              <span className="font-accent text-[1.1em] text-faint">is already out there.</span>
            </h2>
            <div className="mt-10">
              <BrowseCta />
            </div>
            <p className="mt-4 text-[12.5px] text-faint">No account needed to look around.</p>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <Logo />
          <p className="text-[12px] text-faint">
            © {new Date().getFullYear()} {BRAND.name} · Always confirm details on the official source
            before applying.
          </p>
        </div>
      </footer>
    </div>
  );
}
