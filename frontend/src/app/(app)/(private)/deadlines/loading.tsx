import { RowSkeleton } from "@/components/ui/States";

export default function Loading() {
  return (
    <div className="animate-fade-up">
      <div className="pb-6">
        <div className="skeleton h-7 w-44 rounded" />
        <div className="skeleton mt-2.5 h-4 w-96 rounded" />
      </div>
      <div className="space-y-10">
        {Array.from({ length: 2 }, (_, i) => (
          <div key={i} className="pl-5">
            <div className="skeleton mb-3 h-5 w-40 rounded" />
            <RowSkeleton count={3} />
          </div>
        ))}
      </div>
    </div>
  );
}
