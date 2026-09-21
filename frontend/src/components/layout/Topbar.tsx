import { Logo } from "@/components/layout/Logo";
import { MobileNav } from "@/components/layout/Sidebar";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { UserMenu } from "@/components/layout/UserMenu";
import { GlobalSearch } from "@/components/search/GlobalSearch";
import { ButtonLink } from "@/components/ui/Button";
import type { Profile } from "@/lib/types";

export function Topbar({ user }: { user: Profile | null }) {
  return (
    <header className="sticky top-0 z-40 h-14 border-b border-border bg-bg/85 backdrop-blur-md">
      <div className="flex h-full items-center gap-3 px-4 sm:px-5">
        <MobileNav user={user} />
        <Logo href="/dashboard" className="shrink-0" />

        <div className="mx-auto hidden w-full max-w-md md:block">
          <GlobalSearch />
        </div>

        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <ThemeToggle />
          {user ? (
            <UserMenu user={user} />
          ) : (
            <ButtonLink href="/login" size="sm" variant="secondary">
              Sign in
            </ButtonLink>
          )}
        </div>
      </div>
    </header>
  );
}
