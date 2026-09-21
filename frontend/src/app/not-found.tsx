import { ButtonLink } from "@/components/ui/Button";
import { Logo } from "@/components/layout/Logo";

export default function NotFound() {
  return (
    <div className="grid min-h-dvh place-items-center px-4">
      <div className="text-center">
        <Logo className="mx-auto" />
        <h1 className="mt-6 text-[26px] font-semibold tracking-[-0.02em] text-text">
          Page not found
        </h1>
        <p className="mt-2 max-w-sm text-[13.5px] leading-relaxed text-muted">
          That page doesn&apos;t exist. It may have moved, or the link may be out of date.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <ButtonLink href="/dashboard">Go to dashboard</ButtonLink>
          <ButtonLink href="/opportunities" variant="secondary">
            Browse opportunities
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}
