import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { getCurrentUser } from "@/lib/require-user";

/**
 * Shell for the catalogue and every signed-in surface.
 *
 * It does not force a sign-in. Browsing is deliberately open — a visitor can
 * read the catalogue and follow an enrolment link without an account, which is
 * the whole point of the landing page. Pages that genuinely need a user
 * (dashboard, saved, deadlines, profile, admin) guard themselves through
 * `requireUser` in the (private) group's layout.
 */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const profile = await getCurrentUser();

  return (
    <div className="min-h-dvh bg-bg">
      <Topbar user={profile} />
      <div className="mx-auto flex w-full max-w-[1500px]">
        <Sidebar user={profile} />
        <main id="main" className="min-w-0 flex-1 px-4 pb-20 pt-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
