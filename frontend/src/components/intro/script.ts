/**
 * The intro's storyboard.
 *
 * Kept as data rather than markup so the sequence can be reordered or retimed
 * without touching the animation code, and so its total length is checkable.
 * `at` is the progress percentage a beat appears at; the last beat holds until
 * the counter reaches 100.
 */
export type Beat =
  | { at: number; kind: "wordmark" }
  | { at: number; kind: "line"; text: string }
  | { at: number; kind: "list"; label: string; items: string[] }
  | { at: number; kind: "pillars"; items: string[] }
  | { at: number; kind: "finale" };

export const BEATS: Beat[] = [
  { at: 0, kind: "wordmark" },
  { at: 10, kind: "line", text: "The internet is full of opportunities." },
  { at: 25, kind: "line", text: "But they're scattered everywhere." },
  {
    at: 40,
    kind: "list",
    label: "Scattered across",
    items: [
      "CERTIFICATIONS",
      "INTERNSHIPS",
      "HACKATHONS",
      "PROGRAMS",
      "TECH BENEFITS",
      "SCHOLARSHIPS",
    ],
  },
  { at: 55, kind: "line", text: "You shouldn't have to search for them." },
  { at: 70, kind: "pillars", items: ["DISCOVER", "UNDERSTAND", "VERIFY", "MATCH"] },
  { at: 85, kind: "line", text: "Opportunities come to you." },
  {
    at: 95,
    kind: "list",
    label: "Tuned to",
    items: ["Your profile.", "Your interests.", "Your goals.", "Your opportunities."],
  },
  { at: 100, kind: "finale" },
];

/** Total run time. Short on purpose — this plays once, and it must not detain anyone. */
export const DURATION_MS = 7600;

export function beatAt(progress: number): Beat {
  let current = BEATS[0];
  for (const beat of BEATS) {
    if (progress >= beat.at) current = beat;
  }
  return current;
}
