import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/layout/PageHeader";
import { AccountPanel } from "@/components/profile/AccountPanel";
import { ProfileForm } from "@/components/profile/ProfileForm";
import { ErrorState } from "@/components/ui/States";
import { api, ApiError } from "@/lib/api";
import type { Profile } from "@/lib/types";

export const metadata: Metadata = { title: "Profile" };
export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  let profile: Profile;
  try {
    profile = await api.profile();
  } catch (error) {
    return (
      <ErrorState
        title="Could not load your profile"
        message={error instanceof ApiError ? error.message : undefined}
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Your profile"
        description="Everything here feeds the match score on each opportunity. Nothing is shared with the organisations listed."
      />

      <ProfileForm profile={profile} />

      <div className="mt-6">
        <AccountPanel user={profile} />
      </div>

      <section className="mt-8 rounded-panel border border-border bg-bg-subtle p-5">
        <h2 className="text-[13px] font-semibold text-text">How matching works</h2>
        <p className="mt-2 text-[12.5px] leading-relaxed text-muted">
          A match score is the sum of fixed weights: category fit (30), interests (25), skills (20),
          location or remote fit (10), deadline relevance (10) and cost (5). Every point is shown as
          a reason on the opportunity page, so you can always see why something ranked where it did.
          There is no machine learning involved, and the score does not predict whether you will be
          accepted.
        </p>
        <p className="mt-2.5 text-[12.5px] text-muted">
          Your preferences and saved list belong to your account and are not visible to anyone
          else.{" "}
          <Link href="/opportunities" className="text-accent hover:underline">
            Browse the catalogue
          </Link>{" "}
          to see matching applied.
        </p>
      </section>
    </div>
  );
}
