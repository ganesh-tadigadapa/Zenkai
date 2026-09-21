import "server-only";

import { cookies } from "next/headers";

/**
 * The session cookie.
 *
 * The token lives in an httpOnly cookie on the Next.js origin and is forwarded
 * to the API as a Bearer header by `lib/api.ts`. It is therefore never readable
 * by browser JavaScript, which keeps an XSS bug from becoming a session theft.
 */
export const SESSION_COOKIE = "zenkai_session";

const THIRTY_DAYS = 60 * 60 * 24 * 30;

export async function getSessionToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? null;
}

export async function setSessionCookie(token: string): Promise<void> {
  const store = await cookies();
  store.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax", // survives top-level navigation back from an external link
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: THIRTY_DAYS,
  });
}

export async function clearSessionCookie(): Promise<void> {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
}
