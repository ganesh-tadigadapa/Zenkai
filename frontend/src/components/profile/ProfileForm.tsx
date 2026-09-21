"use client";

import { useActionState } from "react";

import { Button } from "@/components/ui/Button";
import { IconCheck, IconAlert } from "@/components/ui/Icons";
import { updateProfileAction, type ActionResult } from "@/lib/actions";
import { CATEGORY_LABELS, cx } from "@/lib/format";
import type { Category, Profile } from "@/lib/types";

const CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[];

const YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate", "Graduated"];

const REMOTE_OPTIONS = [
  { value: "any", label: "Either is fine" },
  { value: "remote", label: "Remote only" },
  { value: "onsite", label: "On-site only" },
];

function Label({ htmlFor, children, hint }: { htmlFor: string; children: string; hint?: string }) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block">
      <span className="text-[13px] font-medium text-text">{children}</span>
      {hint ? <span className="mt-0.5 block text-[11.5px] text-faint">{hint}</span> : null}
    </label>
  );
}

const inputClass =
  "h-10 w-full rounded-lg border border-border bg-surface px-3 text-[13.5px] text-text placeholder:text-faint focus:border-accent focus:outline-none";

function Fieldset({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <fieldset className="rounded-panel border border-border bg-surface p-5 sm:p-6">
      <legend className="px-1 text-[13px] font-semibold text-text">{title}</legend>
      <p className="mb-4 text-[12.5px] leading-relaxed text-muted">{description}</p>
      {children}
    </fieldset>
  );
}

export function ProfileForm({ profile }: { profile: Profile }) {
  const preferences = profile.preferences;

  const [state, formAction, isPending] = useActionState<ActionResult | null, FormData>(
    async (_previous, formData) => updateProfileAction(formData),
    null,
  );

  return (
    <form action={formAction} className="space-y-6">
      <Fieldset
        title="About you"
        description="Used to judge whether you're eligible and where an opportunity is open to you."
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="name">Name</Label>
            <input id="name" name="name" defaultValue={profile.name} className={inputClass} />
          </div>
          <div>
            <Label htmlFor="degree">Degree</Label>
            <input
              id="degree"
              name="degree"
              defaultValue={preferences?.degree ?? ""}
              placeholder="B.Tech, B.Sc, M.Sc…"
              className={inputClass}
            />
          </div>
          <div>
            <Label htmlFor="field_of_study">Field of study</Label>
            <input
              id="field_of_study"
              name="field_of_study"
              defaultValue={preferences?.field_of_study ?? ""}
              placeholder="Computer Science"
              className={inputClass}
            />
          </div>
          <div>
            <Label htmlFor="year">Year</Label>
            <select
              id="year"
              name="year"
              defaultValue={preferences?.year ?? ""}
              className={inputClass}
            >
              <option value="">Select a year</option>
              {YEARS.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="location">Location</Label>
            <input
              id="location"
              name="location"
              defaultValue={preferences?.location ?? ""}
              placeholder="Bengaluru, India"
              className={inputClass}
            />
          </div>
          <div>
            <Label htmlFor="remote_preference">Remote preference</Label>
            <select
              id="remote_preference"
              name="remote_preference"
              defaultValue={preferences?.remote_preference ?? "any"}
              className={inputClass}
            >
              {REMOTE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Fieldset>

      <Fieldset
        title="Skills and interests"
        description="Matching compares these against each opportunity's skills and tags. Separate entries with commas."
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="skills" hint="Things you can already do">
              Skills
            </Label>
            <input
              id="skills"
              name="skills"
              defaultValue={preferences?.skills.join(", ") ?? ""}
              placeholder="Python, React, Docker, SQL"
              className={inputClass}
            />
          </div>
          <div>
            <Label htmlFor="interests" hint="Areas you want to move towards">
              Interests
            </Label>
            <input
              id="interests"
              name="interests"
              defaultValue={preferences?.interests.join(", ") ?? ""}
              placeholder="Cloud, DevOps, AI, Web Development"
              className={inputClass}
            />
          </div>
        </div>
      </Fieldset>

      <Fieldset
        title="What you're looking for"
        description="Opportunities in the categories you pick score higher in your recommendations."
      >
        <div className="grid gap-2 sm:grid-cols-2">
          {CATEGORIES.map((category) => {
            const checked = preferences?.preferred_categories.includes(category) ?? false;
            return (
              <label
                key={category}
                className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-border px-3 py-2.5 transition-colors hover:border-border-strong hover:bg-bg-subtle has-[:checked]:border-accent has-[:checked]:bg-accent-soft"
              >
                <input
                  type="checkbox"
                  name="preferred_categories"
                  value={category}
                  defaultChecked={checked}
                  className="size-3.5 shrink-0 accent-[var(--accent)]"
                />
                <span className="text-[13px] font-medium text-text">
                  {CATEGORY_LABELS[category]}
                </span>
              </label>
            );
          })}
        </div>
      </Fieldset>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={isPending}>
          {isPending ? "Saving…" : "Save preferences"}
        </Button>

        {state ? (
          <p
            role="status"
            className={cx(
              "inline-flex items-center gap-1.5 text-[13px]",
              state.ok ? "text-verified" : "text-expired",
            )}
          >
            {state.ok ? <IconCheck /> : <IconAlert />}
            {state.message ?? (state.ok ? "Saved." : "Could not save.")}
          </p>
        ) : null}
      </div>
    </form>
  );
}
