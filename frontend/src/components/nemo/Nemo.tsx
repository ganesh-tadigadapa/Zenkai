"use client";

import Link from "next/link";
import { useEffect, useRef, useState, useTransition } from "react";

import { IconArrowRight, IconChat, IconSend, IconX } from "@/components/ui/Icons";
import { askNemoAction } from "@/lib/actions";
import { CATEGORY_SHORT, cx, deadlineLabel } from "@/lib/format";
import type { NemoReply, Opportunity } from "@/lib/types";

type Message =
  | { from: "student"; text: string }
  | { from: "nemo"; text: string; results?: Opportunity[]; browseUrl?: string | null; suggestions?: string[] };

const STORAGE_KEY = "zenkai:nemo";

// Shown straight away rather than fetched, so opening the panel is instant even
// while the API is still waking up. Mirrors the backend's INTRO.
const INTRO: Message = {
  from: "nemo",
  text:
    "Hi, I'm Nemo. I help you find internships, hackathons, certifications, scholarships " +
    "and programs on Zenkai. Tell me what you're after in your own words, like " +
    "“free Python certifications” or “remote internships closing this week”.",
  suggestions: [
    "Internships closing this week",
    "Free AI certifications",
    "Hackathons this month",
    "I'm a beginner, where do I start?",
  ],
};

const UNREACHABLE =
  "I couldn't reach Zenkai just then. If the site has been quiet for a while it may be " +
  "waking up, so give it a few seconds and try again.";

function load(): Message[] {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored) as Message[];
  } catch {
    // unreadable or blocked - start fresh
  }
  return [INTRO];
}

function fromReply(answer: NemoReply): Message {
  return {
    from: "nemo",
    text: answer.reply,
    results: answer.opportunities,
    browseUrl: answer.browse_url,
    suggestions: answer.suggestions,
  };
}

/** Nemo: a small guide that turns plain questions into catalogue searches. */
export function Nemo() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([INTRO]);
  const [draft, setDraft] = useState("");
  const [pending, startTransition] = useTransition();
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // The conversation is restored on first open rather than on mount, so the
  // server render and the first client render agree.
  const restored = useRef(false);

  useEffect(() => {
    if (!restored.current) return;
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-30)));
    } catch {
      // not persisting is fine
    }
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  function toggle() {
    if (!restored.current) {
      restored.current = true;
      setMessages(load());
    }
    setOpen((value) => !value);
  }

  function send(text: string) {
    const message = text.trim();
    if (!message || pending) return;
    setDraft("");
    setMessages((current) => [...current, { from: "student", text: message }]);
    startTransition(async () => {
      const result = await askNemoAction(message);
      setMessages((current) => [
        ...current,
        result.ok && result.answer ? fromReply(result.answer) : { from: "nemo", text: UNREACHABLE },
      ]);
    });
  }

  function startOver() {
    setMessages([INTRO]);
    inputRef.current?.focus();
  }

  // On a phone the panel covers the page, so following a link should close it.
  function closeOnSmallScreens() {
    if (window.matchMedia("(max-width: 639px)").matches) setOpen(false);
  }

  const last = messages[messages.length - 1];

  return (
    <>
      {open && (
        <section
          role="dialog"
          aria-label="Nemo, your opportunity guide"
          className={cx(
            "animate-fade-up fixed z-40 flex flex-col overflow-hidden",
            "rounded-panel border border-border bg-surface shadow-panel",
            "inset-x-3 bottom-[4.75rem] top-16 sm:inset-x-auto sm:top-auto sm:right-5",
            "sm:h-[min(600px,calc(100dvh-8rem))] sm:w-[400px]",
          )}
        >
          <header className="flex items-center gap-3 border-b border-border px-4 py-3">
            <span
              aria-hidden
              className="grid size-9 place-items-center rounded-full bg-accent text-[15px] font-semibold text-white"
            >
              N
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[15px] font-semibold text-text">Nemo</p>
              <p className="truncate text-[12px] text-muted">Your opportunity guide</p>
            </div>
            {messages.length > 1 && (
              <button
                type="button"
                onClick={startOver}
                className="rounded-md px-2 py-1 text-[12px] text-muted hover:bg-bg-subtle hover:text-text"
              >
                Start over
              </button>
            )}
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close Nemo"
              className="grid size-8 place-items-center rounded-md text-muted hover:bg-bg-subtle hover:text-text"
            >
              <IconX className="text-[16px]" />
            </button>
          </header>

          <div
            ref={logRef}
            aria-live="polite"
            className="flex-1 space-y-4 overflow-y-auto overscroll-contain px-4 py-4"
          >
            {messages.map((message, index) =>
              message.from === "student" ? (
                <p
                  key={index}
                  className="ml-auto w-fit max-w-[85%] rounded-card rounded-br-sm bg-accent px-3.5 py-2 text-[14px] leading-relaxed text-white"
                >
                  {message.text}
                </p>
              ) : (
                <div key={index} className="max-w-[92%] space-y-2.5">
                  <p className="w-fit whitespace-pre-line rounded-card rounded-bl-sm bg-bg-subtle px-3.5 py-2.5 text-[14px] leading-relaxed text-text">
                    {message.text}
                  </p>

                  {message.results && message.results.length > 0 && (
                    <ul className="space-y-1.5">
                      {message.results.map((opportunity) => (
                        <li key={opportunity.id}>
                          <Link
                            href={`/opportunities/${opportunity.slug}`}
                            onClick={closeOnSmallScreens}
                            className="block rounded-card border border-border bg-surface px-3 py-2.5 transition-colors hover:border-border-strong hover:bg-bg-subtle"
                          >
                            <span className="line-clamp-2 text-[13.5px] font-medium leading-snug text-text">
                              {opportunity.title}
                            </span>
                            <span className="mt-1 flex flex-wrap gap-x-2 text-[12px] text-muted">
                              <span className="truncate">{opportunity.organization.name}</span>
                              <span aria-hidden>·</span>
                              <span>{CATEGORY_SHORT[opportunity.category]}</span>
                              <span aria-hidden>·</span>
                              <span className="tnum">{deadlineLabel(opportunity)}</span>
                            </span>
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}

                  {message.browseUrl && (
                    <Link
                      href={message.browseUrl}
                      onClick={closeOnSmallScreens}
                      className="inline-flex items-center gap-1 text-[13px] font-medium text-accent hover:text-accent-hover"
                    >
                      See all on Zenkai <IconArrowRight className="text-[14px]" />
                    </Link>
                  )}
                </div>
              ),
            )}

            {pending && (
              <div
                aria-label="Nemo is typing"
                className="flex w-fit gap-1 rounded-card rounded-bl-sm bg-bg-subtle px-3.5 py-3"
              >
                {[0, 150, 300].map((delay) => (
                  <span
                    key={delay}
                    className="size-1.5 animate-bounce rounded-full bg-muted"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
            )}

            {!pending && last.from === "nemo" && last.suggestions && last.suggestions.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {last.suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => send(suggestion)}
                    className="rounded-full border border-border bg-surface px-3 py-1.5 text-[12.5px] text-text transition-colors hover:border-accent hover:text-accent"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              send(draft);
            }}
            className="flex items-center gap-2 border-t border-border p-3"
          >
            <label htmlFor="nemo-input" className="sr-only">
              Message Nemo
            </label>
            <input
              id="nemo-input"
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              maxLength={500}
              autoComplete="off"
              placeholder="Ask about internships, hackathons…"
              className="h-10 min-w-0 flex-1 rounded-[10px] border border-border bg-bg px-3 text-[14px] text-text placeholder:text-faint focus:border-accent focus:outline-none"
            />
            <button
              type="submit"
              disabled={!draft.trim() || pending}
              aria-label="Send"
              className="grid size-10 shrink-0 place-items-center rounded-[10px] bg-accent text-white transition-colors hover:bg-accent-hover disabled:opacity-40"
            >
              <IconSend className="text-[18px]" />
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        aria-label={open ? "Close Nemo" : "Ask Nemo, your opportunity guide"}
        className={cx(
          "fixed bottom-4 right-4 z-40 flex h-12 items-center gap-2 rounded-full px-4 sm:bottom-5 sm:right-5",
          "bg-accent text-white shadow-float transition-[transform,background-color] duration-200",
          "hover:-translate-y-0.5 hover:bg-accent-hover",
        )}
      >
        {open ? <IconX className="text-[20px]" /> : <IconChat className="text-[20px]" />}
        <span className="text-[14px] font-medium">{open ? "Close" : "Ask Nemo"}</span>
      </button>
    </>
  );
}
