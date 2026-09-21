import { cx } from "@/lib/format";

/**
 * The hero visualisation: concentric rings with a sweeping arm and category
 * blips. Pure SVG + CSS so it costs nothing at runtime, respects
 * prefers-reduced-motion, and stays crisp at any size.
 */
const BLIPS: { angle: number; radius: number; label: string; delay: string }[] = [
  { angle: 25, radius: 0.82, label: "Certifications", delay: "0s" },
  { angle: 95, radius: 0.55, label: "Internships", delay: "1.1s" },
  { angle: 160, radius: 0.88, label: "Hackathons", delay: "2.2s" },
  { angle: 215, radius: 0.42, label: "Programs", delay: "0.6s" },
  { angle: 285, radius: 0.72, label: "Tech Benefits", delay: "1.7s" },
  { angle: 330, radius: 0.34, label: "Scholarships", delay: "2.8s" },
];

const SIZE = 320;
const CENTER = SIZE / 2;
const MAX_RADIUS = CENTER - 14;

function position(angle: number, radius: number) {
  const radians = ((angle - 90) * Math.PI) / 180;
  return {
    x: CENTER + Math.cos(radians) * radius * MAX_RADIUS,
    y: CENTER + Math.sin(radians) * radius * MAX_RADIUS,
  };
}

export function Radar({ className }: { className?: string }) {
  return (
    <div className={cx("relative aspect-square w-full max-w-[420px]", className)}>
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="size-full"
        role="img"
        aria-label="A radar sweeping across the six Zenkai categories: certifications, internships, hackathons, programs, tech benefits and scholarships."
      >
        <defs>
          <radialGradient id="radar-glow">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.16" />
            <stop offset="70%" stopColor="var(--accent)" stopOpacity="0.04" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="sweep-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.32" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </linearGradient>
        </defs>

        <circle cx={CENTER} cy={CENTER} r={MAX_RADIUS} fill="url(#radar-glow)" />

        {[0.28, 0.52, 0.76, 1].map((ratio) => (
          <circle
            key={ratio}
            cx={CENTER}
            cy={CENTER}
            r={MAX_RADIUS * ratio}
            fill="none"
            stroke="var(--border-strong)"
            strokeWidth="1"
            strokeOpacity={ratio === 1 ? 0.9 : 0.45}
          />
        ))}

        {[0, 60, 120].map((angle) => (
          <line
            key={angle}
            x1={CENTER - MAX_RADIUS}
            y1={CENTER}
            x2={CENTER + MAX_RADIUS}
            y2={CENTER}
            stroke="var(--border-strong)"
            strokeWidth="1"
            strokeOpacity="0.35"
            transform={`rotate(${angle} ${CENTER} ${CENTER})`}
          />
        ))}

        {/* Sweeping arm */}
        <g
          style={{
            transformOrigin: `${CENTER}px ${CENTER}px`,
            animation: "radar-sweep 8s linear infinite",
          }}
        >
          <path
            d={`M ${CENTER} ${CENTER} L ${CENTER} ${CENTER - MAX_RADIUS} A ${MAX_RADIUS} ${MAX_RADIUS} 0 0 1 ${
              CENTER + MAX_RADIUS * 0.72
            } ${CENTER - MAX_RADIUS * 0.7} Z`}
            fill="url(#sweep-gradient)"
          />
          <line
            x1={CENTER}
            y1={CENTER}
            x2={CENTER}
            y2={CENTER - MAX_RADIUS}
            stroke="var(--accent)"
            strokeWidth="1.5"
            strokeOpacity="0.7"
          />
        </g>

        {BLIPS.map((blip) => {
          const { x, y } = position(blip.angle, blip.radius);
          return (
            <g key={blip.label}>
              <circle
                cx={x}
                cy={y}
                r="9"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="1.2"
                style={{
                  transformOrigin: `${x}px ${y}px`,
                  animation: `radar-ping 8s ease-out ${blip.delay} infinite`,
                }}
              />
              <circle cx={x} cy={y} r="3" fill="var(--accent)" />
            </g>
          );
        })}

        <circle cx={CENTER} cy={CENTER} r="4" fill="var(--text)" />
      </svg>
    </div>
  );
}
