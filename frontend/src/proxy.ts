import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/session";

/**
 * Sends a signed-out visitor to sign-in, remembering where they were going.
 *
 * This only checks that a session cookie exists. Validating it belongs in the
 * private layout, which can call the API; middleware runs on every matched
 * request and should not add a network round trip to each one. The layout is
 * the real gate — this exists so the `next` parameter names the route the
 * person actually asked for, which a layout cannot know.
 */
const PRIVATE_PREFIXES = ["/dashboard", "/saved", "/deadlines", "/profile", "/admin"];

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const isPrivate = PRIVATE_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
  if (!isPrivate) return NextResponse.next();

  if (request.cookies.has(SESSION_COOKIE)) return NextResponse.next();

  const login = new URL("/login", request.url);
  login.searchParams.set("next", pathname + search);
  return NextResponse.redirect(login);
}

export const config = {
  // Everything except Next's own assets and static files.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
