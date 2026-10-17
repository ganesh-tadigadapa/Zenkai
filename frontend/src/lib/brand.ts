/**
 * Brand constants.
 *
 * Kept in one place so copy stays consistent and a future rename is a
 * single-file change rather than a repository-wide search.
 */
export const BRAND = {
  name: "Zenkai",
  wordmark: "ZENKAI",
  /** The public address. Link previews and canonical URLs are built from it. */
  url: "https://getzenkai.vercel.app",
  tagline: "Your opportunity radar.",
  hero: "Stop searching. Start discovering.",
  description:
    "Zenkai discovers opportunities scattered across the web — from internships and hackathons to certifications, scholarships, programs, and student benefits — and brings the ones relevant to you into one place.",
  /** Short form for metadata and cards, where the full sentence is too long. */
  shortDescription:
    "An opportunity intelligence platform for students. Certifications, internships, hackathons, programs, tech benefits and scholarships — with the official source on every record.",
} as const;

/** Storage keys, namespaced so they cannot collide with anything else. */
export const STORAGE_KEYS = {
  theme: "zenkai-theme",
} as const;
