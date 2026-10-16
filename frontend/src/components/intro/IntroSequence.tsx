"use client";

import Link from "next/link";
import {
  type CSSProperties,
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

import { LogoMark } from "@/components/layout/Logo";
import { BRAND, STORAGE_KEYS } from "@/lib/brand";
import { cx } from "@/lib/format";

import { beatAt, DURATION_MS, type Beat } from "./script";

/**
 * The entrance sequence.
 *
 * Constraints it is built around:
 *   * It plays once. Returning visitors go straight to the site.
 *   * It is skippable at all times, by click, Escape or Space.
 *   * `prefers-reduced-motion` skips it outright rather than showing a
 *     shortened version — someone who asked for less motion did not ask for a
 *     faster cinematic.
 *   * It renders nothing on the server, so there is no flash of the intro for
 *     visitors who have already seen it.
 */
/**
 * Whether this visitor should see the intro.
 *
 * Read through an external store rather than an effect: both inputs live
 * outside React, the answer cannot change mid-session, and the server snapshot
 * is always `false` so the overlay never appears in server-rendered HTML.
 */
function subscribe() {
  return () => {};
}

function clientSnapshot(): boolean {
  try {
    if (localStorage.getItem(STORAGE_KEYS.introSeen) === "1") return false;
  } catch {
    /* storage blocked — treat as unseen */
  }
  // Someone who asked for less motion did not ask for a faster cinematic.
  return !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

const serverSnapshot = () => false;

export function IntroSequence() {
  const shouldPlay = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
  const [state, setState] = useState<"playing" | "leaving" | "done">("playing");
  const [progress, setProgress] = useState(0);
  const frame = useRef<number | null>(null);
  const startedAt = useRef<number | null>(null);
  const skipRef = useRef<HTMLButtonElement | null>(null);

  const active = shouldPlay && state !== "done";

  const finish = useCallback((immediate = false) => {
    if (frame.current !== null) cancelAnimationFrame(frame.current);
    try {
      localStorage.setItem(STORAGE_KEYS.introSeen, "1");
    } catch {
      /* private browsing — it will simply play again next time */
    }
    document.documentElement.style.removeProperty("overflow");
    // Release the landing page's held entrance so it plays as the overlay fades.
    delete document.documentElement.dataset.intro;
    setState(immediate ? "done" : "leaving");
  }, []);

  // The landing page holds its entrance when it expects the intro. If the
  // intro then does not play, release it straight away. Checks the client
  // snapshot directly: during hydration `shouldPlay` briefly reports the
  // server value, false, even when the intro is about to play.
  useEffect(() => {
    if (!clientSnapshot()) delete document.documentElement.dataset.intro;
  }, []);

  // Lock scroll only while the overlay actually owns the viewport, and move
  // focus into the dialog so a keyboard user's first Tab lands on Skip rather
  // than on the page behind the overlay.
  useEffect(() => {
    if (!active) return;
    document.documentElement.style.overflow = "hidden";
    skipRef.current?.focus();
    return () => {
      document.documentElement.style.removeProperty("overflow");
    };
  }, [active]);

  // Drive the counter from real elapsed time, so a slow frame cannot stretch
  // the sequence or leave the number out of step with the beats.
  useEffect(() => {
    if (!active || state !== "playing") return;

    function step(now: number) {
      startedAt.current ??= now;
      const elapsed = now - startedAt.current;
      const pct = Math.min(100, (elapsed / DURATION_MS) * 100);
      setProgress(pct);
      if (pct < 100) {
        frame.current = requestAnimationFrame(step);
      } else {
        // Let the finale hold briefly before the site appears.
        window.setTimeout(() => finish(), 1400);
      }
    }
    frame.current = requestAnimationFrame(step);
    return () => {
      if (frame.current !== null) cancelAnimationFrame(frame.current);
    };
  }, [active, state, finish]);

  // Skip affordances.
  useEffect(() => {
    if (!active || state !== "playing") return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape" || event.key === " " || event.key === "Enter") {
        event.preventDefault();
        finish();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [active, state, finish]);

  if (!active) return null;

  const beat = beatAt(progress);
  const rounded = Math.round(progress);
  const leaving = state === "leaving";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`${BRAND.name} introduction`}
      className={cx(
        "fixed inset-0 z-[100] flex flex-col overflow-hidden bg-bg",
        "transition-opacity duration-[600ms] ease-out",
        leaving ? "pointer-events-none opacity-0" : "opacity-100",
      )}
      onTransitionEnd={() => leaving && setState("done")}
    >
      {/* Ambient field: one restrained radial wash, not a particle system. */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div
          className="absolute left-1/2 top-1/2 size-[min(140vw,1100px)] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-[0.55] transition-transform duration-1000 ease-out"
          style={{
            background:
              "radial-gradient(circle, color-mix(in srgb, var(--accent) 16%, transparent) 0%, transparent 62%)",
            transform: `translate(-50%, -50%) scale(${0.72 + progress / 165})`,
          }}
        />
        <IntroRings progress={progress} />
      </div>

      {/* Top bar: mark, progress, skip. */}
      <header className="relative z-10 flex items-center justify-between px-5 pt-5 sm:px-8 sm:pt-7">
        <div className="flex items-center gap-2.5">
          <LogoMark />
          <span className="text-[12px] font-semibold tracking-[0.18em] text-faint">ZENKAI</span>
        </div>

        <button
          ref={skipRef}
          type="button"
          onClick={() => finish()}
          className="rounded-lg px-3 py-1.5 text-[12.5px] font-medium text-muted transition-colors hover:bg-bg-subtle hover:text-text"
        >
          Skip
          <span className="sr-only"> introduction</span>
        </button>
      </header>

      {/* Stage */}
      <div className="relative z-10 flex flex-1 items-center justify-center px-6 py-10">
        <div className="w-full max-w-2xl text-center">
          <Stage beat={beat} progress={progress} onEnter={() => finish()} />
        </div>
      </div>

      <span aria-live="polite" className="sr-only">
        {rounded === 100 ? `${BRAND.name}. ${BRAND.tagline}` : null}
      </span>
    </div>
  );
}

/** Where blips light up on the radar, and the progress at which each appears. */
const BLIPS = [
  { x: 262, y: 128, at: 12 },
  { x: 118, y: 160, at: 28 },
  { x: 300, y: 250, at: 42 },
  { x: 150, y: 292, at: 58 },
  { x: 232, y: 330, at: 74 },
  { x: 92, y: 226, at: 88 },
];

/** Concentric rings that tighten as the sequence advances, with a sweep picking up blips. */
function IntroRings({ progress }: { progress: number }) {
  return (
    <>
      <div
        className="absolute left-1/2 top-1/2 size-[min(110vw,720px)] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-full"
        style={{ maskImage: "radial-gradient(circle, black 0%, black 46%, transparent 47%)" }}
      >
        <div
          className="size-full"
          style={{
            background:
              "conic-gradient(from 0deg, transparent 0deg, transparent 300deg, color-mix(in srgb, var(--accent) 22%, transparent) 360deg)",
            animation: "intro-sweep 3.2s linear infinite",
          }}
        />
      </div>
      <svg
        viewBox="0 0 400 400"
        className="absolute left-1/2 top-1/2 size-[min(110vw,720px)] -translate-x-1/2 -translate-y-1/2"
        aria-hidden
      >
        {[70, 118, 166].map((radius, index) => (
          <circle
            key={radius}
            cx="200"
            cy="200"
            r={radius}
            fill="none"
            stroke="var(--border-strong)"
            strokeWidth="1"
            strokeOpacity={0.22 + (progress / 100) * 0.38}
            strokeDasharray={index === 1 ? "2 7" : undefined}
            style={{
              transformOrigin: "200px 200px",
              transform: `rotate(${progress * (index % 2 === 0 ? 0.9 : -0.6)}deg)`,
            }}
          />
        ))}
        {BLIPS.filter((blip) => progress >= blip.at).map((blip) => (
          <g key={`${blip.x}-${blip.y}`}>
            <circle
              cx={blip.x}
              cy={blip.y}
              r="9"
              fill="none"
              stroke="var(--accent)"
              strokeWidth="1"
              style={{
                transformOrigin: `${blip.x}px ${blip.y}px`,
                animation: "intro-ping 1.6s ease-out infinite",
              }}
            />
            <circle
              cx={blip.x}
              cy={blip.y}
              r="3"
              fill="var(--accent)"
              className="animate-fade-up"
              style={{ transformOrigin: `${blip.x}px ${blip.y}px` }}
            />
          </g>
        ))}
      </svg>
    </>
  );
}

/** Per-letter / per-word entrance delay. */
const delay = (ms: number) => ({ "--d": `${ms}ms` }) as CSSProperties;

/** The wordmark, assembling one letter at a time. */
function Wordmark() {
  return (
    <h1 className="text-[clamp(2.5rem,12vw,5.5rem)] font-semibold leading-none tracking-[0.16em] text-text">
      {"ZENKAI".split("").map((letter, index) => (
        <span
          key={index}
          className={cx("animate-letter-in", index >= 3 && "text-accent")}
          style={delay(index * 70)}
        >
          {letter}
        </span>
      ))}
    </h1>
  );
}

/** A sentence that arrives word by word. */
function Words({ text }: { text: string }) {
  return (
    <>
      {text.split(" ").map((word, index) => (
        <span key={index} className="animate-letter-in" style={delay(index * 65)}>
          {word}
          {"\u00a0"}
        </span>
      ))}
    </>
  );
}

function Stage({
  beat,
  progress,
  onEnter,
}: {
  beat: Beat;
  progress: number;
  onEnter: () => void;
}) {
  // Keying on the beat restarts the entrance animation for each new one.
  const key = `${beat.kind}-${beat.at}`;

  if (beat.kind === "wordmark") {
    return (
      <div key={key}>
        <Wordmark />
      </div>
    );
  }

  if (beat.kind === "line") {
    return (
      <p
        key={key}
        className="text-balance text-[clamp(1.35rem,4.5vw,2.25rem)] font-medium leading-snug tracking-[-0.02em] text-text"
      >
        <Words text={beat.text} />
      </p>
    );
  }

  if (beat.kind === "list") {
    /*
      Every item holds its place from the start and brightens in turn. Hiding
      them outright would leave the revealed ones off-centre while the rest of
      the row sat empty, which reads as a layout bug rather than a reveal.
    */
    return (
      <div key={key} className="animate-fade-up">
        <p className="mb-6 text-[11px] uppercase tracking-[0.18em] text-faint">{beat.label}</p>
        <ul className="flex flex-wrap items-center justify-center gap-x-3 gap-y-2.5">
          {beat.items.map((item, index) => {
            const shown = progress >= beat.at + index * 1.4;
            return (
              <li
                key={item}
                className={cx(
                  "rounded-lg border px-3 py-1.5 text-[12.5px] font-medium tracking-[0.06em] sm:text-[13.5px]",
                  "transition-all duration-500 ease-out",
                  shown
                    ? "border-border bg-surface/70 text-text opacity-100 backdrop-blur-sm"
                    : "border-transparent bg-transparent text-faint opacity-35",
                )}
              >
                {item}
              </li>
            );
          })}
        </ul>
      </div>
    );
  }

  if (beat.kind === "pillars") {
    return (
      <div key={key}>
        <p className="mb-7 text-[11px] uppercase tracking-[0.18em] text-faint">
          Opportunity intelligence
        </p>
        <ol className="grid grid-cols-2 gap-px overflow-hidden rounded-panel border border-border bg-border sm:grid-cols-4">
          {beat.items.map((item, index) => {
            const shown = progress >= beat.at + index * 2.4;
            return (
              <li
                key={item}
                className={cx(
                  "bg-surface px-3 py-5 transition-opacity duration-500",
                  shown ? "opacity-100" : "opacity-25",
                )}
              >
                <span className="tnum block text-[10px] text-faint">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="mt-1.5 block text-[12.5px] font-semibold tracking-[0.08em] text-text sm:text-[13.5px]">
                  {item}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    );
  }

  // Finale
  return (
    <div key={key}>
      <Wordmark />
      <p
        className="animate-blur-in mt-5 text-[clamp(1rem,3vw,1.4rem)] font-medium text-muted"
        style={delay(450)}
      >{BRAND.tagline}</p>
      {/* Dismisses the overlay and navigates client-side, so the site fades in
          rather than the browser reloading into it. */}
      <Link
        href="/opportunities"
        onClick={onEnter}
        className="animate-blur-in mt-9 inline-flex h-12 items-center gap-2 rounded-full bg-text px-7 text-[15px] font-medium text-bg transition-opacity hover:opacity-85"
        style={delay(650)}
      >
        Enter Zenkai
        <span aria-hidden>→</span>
      </Link>
    </div>
  );
}
