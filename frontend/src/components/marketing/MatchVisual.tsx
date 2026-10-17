import { vars } from "@/lib/style";

/** Feature card art: the signals a recommendation is scored on. */
export function MatchVisual() {
  const bars = [
    { label: "Category", w: 1 },
    { label: "Interests", w: 0.85 },
    { label: "Skills", w: 0.65 },
    { label: "Location", w: 0.9 },
  ];
  return (
    <div className="flex h-full flex-col justify-center gap-3.5 px-2">
      {bars.map((bar, index) => (
        <div key={bar.label} className="grid grid-cols-[72px_1fr] items-center gap-3">
          <span className="text-[11.5px] text-faint">{bar.label}</span>
          <span className="h-2 overflow-hidden rounded-full bg-bg-subtle">
            <span
              className="bar-fill block h-full rounded-full bg-gradient-to-r from-accent/60 to-accent"
              style={vars({ "--w": bar.w, "--d": `${index * 180}ms` })}
            />
          </span>
        </div>
      ))}
    </div>
  );
}
