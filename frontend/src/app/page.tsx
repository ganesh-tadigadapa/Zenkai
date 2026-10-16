import type { Metadata } from "next";
import { Instrument_Serif } from "next/font/google";
import Link from "next/link";
import type { CSSProperties } from "react";

import { GuestButton } from "@/components/auth/GuestButton";
import { IntroSequence } from "@/components/intro/IntroSequence";
import { Logo } from "@/components/layout/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Spotlight } from "@/components/marketing/Spotlight";
import { ButtonLink } from "@/components/ui/Button";
import {
  IconArrowRight,
  IconAward,
  IconBriefcase,
  IconGraduationCap,
  IconSparkles,
  IconTrophy,
  IconUsers,
} from "@/components/ui/Icons";
import { BRAND, STORAGE_KEYS } from "@/lib/brand";

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

/*
  Runs before the hero paints. If the intro is about to play, this holds the
  page's entrance animation until the overlay leaves (IntroSequence clears the
  flag), so the reveal is seen rather than spent behind the overlay. It mirrors
  the intro's own check: first visit, motion allowed.
*/
const HOLD_FOR_INTRO = `
(function () {
  try {
    if (localStorage.getItem('${STORAGE_KEYS.introSeen}') === '1') return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    document.documentElement.dataset.intro = 'pending';
  } catch (e) {}
})();
`;

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

export default function LandingPage() {
  return (
    <div className={`${serif.variable} min-h-dvh overflow-x-clip bg-bg`}>
      <script dangerouslySetInnerHTML={{ __html: HOLD_FOR_INTRO }} />
      {/*
        Plays once per visitor, on the client only. Returning visitors and
        anyone with prefers-reduced-motion never see it, and it renders nothing
        server-side so the landing page is complete without it.
      */}
      <IntroSequence />
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
