import { vars } from "@/lib/style";

/** An endless horizontal scroll of its children that pauses on hover. */
export function Marquee({
  children,
  reverse = false,
  speed = "40s",
}: {
  children: React.ReactNode[];
  reverse?: boolean;
  speed?: string;
}) {
  return (
    <div
      className="overflow-hidden"
      style={{
        maskImage: "linear-gradient(to right, transparent, black 12%, black 88%, transparent)",
      }}
    >
      {/* Two copies, so the loop is seamless at -50%. The second is hidden from screen readers. */}
      <div
        className={`${reverse ? "animate-marquee-reverse" : "animate-marquee"} flex w-max hover:[animation-play-state:paused]`}
        style={vars({ "--speed": speed })}
      >
        <ul className="flex shrink-0 items-center gap-4 pr-4">{children}</ul>
        <ul aria-hidden className="flex shrink-0 items-center gap-4 pr-4">
          {children}
        </ul>
      </div>
    </div>
  );
}
