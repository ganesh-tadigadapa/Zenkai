import { GridSkeleton } from "@/components/ui/States";

export default function Loading() {
  return (
    <div className="animate-fade-up">
      <div className="pb-6">
        <div className="skeleton h-7 w-56 rounded" />
        <div className="skeleton mt-2.5 h-4 w-80 rounded" />
      </div>
      <GridSkeleton count={6} />
    </div>
  );
}
