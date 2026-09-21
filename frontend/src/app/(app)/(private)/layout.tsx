import { requireUser } from "@/lib/require-user";

/**
 * Guards every personal surface: dashboard, saved, deadlines, profile, admin.
 *
 * The check lives in a layout rather than in each page because a layout runs
 * before the page's Suspense boundary. Guarding inside a page that has a
 * `loading.tsx` would stream a 200 first, leaving the redirect to happen
 * client-side — correct for a browser, but a crawler or API client would see a
 * 200 for a page it cannot read.
 *
 * The route group name is in parentheses, so it does not appear in any URL.
 */
export default async function PrivateLayout({ children }: { children: React.ReactNode }) {
  await requireUser("/dashboard");
  return <>{children}</>;
}
