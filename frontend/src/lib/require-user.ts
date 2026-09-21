import "server-only";

import { redirect } from "next/navigation";

import { api, ApiError } from "./api";
import { getSessionToken } from "./session";
import type { Profile } from "./types";

/**
 * The signed-in user, or null.
 *
 * Resolves the session against the API rather than trusting that a cookie
 * exists. A cookie can outlive its session — it expires after 30 days, is
 * revoked by signing out elsewhere or changing a password, and disappears
 * whenever the database is reseeded. Treating presence as proof of validity
 * caused an infinite redirect loop between /login and the private routes.
 */
export async function getCurrentUser(): Promise<Profile | null> {
  if (!(await getSessionToken())) return null;
  try {
    return await api.profile();
  } catch (error) {
    // 401 means the session is gone. Anything else means the API is
    // unreachable, which callers surface as an error state rather than as a
    // sign-in prompt — but neither case is a signed-in user.
    if (!(error instanceof ApiError)) throw error;
    return null;
  }
}

/**
 * Guard for pages that are meaningless without an account.
 *
 * Redirects to sign-in with `next` so the person lands back where they were
 * going, and with `expired` when they held a cookie that no longer resolves, so
 * the sign-in page can explain why they are seeing it.
 */
export async function requireUser(next: string): Promise<Profile> {
  const user = await getCurrentUser();
  if (user) return user;

  const params = new URLSearchParams({ next });
  if (await getSessionToken()) params.set("expired", "1");
  redirect(`/login?${params.toString()}`);
}
