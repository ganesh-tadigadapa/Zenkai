import { EmptyState } from "@/components/ui/States";

export default function OpportunityNotFound() {
  return (
    <div className="mx-auto max-w-xl py-16">
      <EmptyState
        title="That opportunity isn't here"
        body="It may have been removed by a reviewer, or the link may be out of date."
        action={{ href: "/opportunities", label: "Browse all opportunities" }}
      />
    </div>
  );
}
