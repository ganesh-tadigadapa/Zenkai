export default function Loading() {
  return (
    <div className="animate-fade-up mx-auto max-w-3xl" aria-busy="true">
      <div className="pb-6">
        <div className="skeleton h-7 w-48 rounded" />
        <div className="skeleton mt-2.5 h-4 w-80 rounded" />
      </div>
      <div className="space-y-6">
        <div className="skeleton h-64 rounded-panel" />
        <div className="skeleton h-44 rounded-panel" />
        <div className="skeleton h-52 rounded-panel" />
      </div>
      <span className="sr-only">Loading your profile…</span>
    </div>
  );
}
