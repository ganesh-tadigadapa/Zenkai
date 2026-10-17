import { GuestButton } from "@/components/auth/GuestButton";
import { ButtonLink } from "@/components/ui/Button";
import { IconArrowRight } from "@/components/ui/Icons";

/** The one call to action, with a light travelling round its edge. */
export function PrimaryCta({ children }: { children: React.ReactNode }) {
  return (
    <span className="glow-border isolate">
      <GuestButton variant="ink" className="rounded-full px-8">
        {children}
      </GuestButton>
    </span>
  );
}

/** The closing call to action: same glow, but leads into the catalogue. */
export function BrowseCta() {
  return (
    <span className="glow-border isolate">
      <ButtonLink href="/opportunities" variant="ink" size="lg" className="group rounded-full px-8">
        Browse opportunities
        <IconArrowRight className="transition-transform group-hover:translate-x-0.5" />
      </ButtonLink>
    </span>
  );
}
