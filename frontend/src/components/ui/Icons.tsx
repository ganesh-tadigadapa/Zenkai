/**
 * Inline SVG icons.
 *
 * Hand-rolled rather than pulled from an icon package: the set is small, and
 * inlining keeps the client bundle free of a dependency for ~20 glyphs.
 * All icons inherit `currentColor` and are hidden from assistive technology —
 * the surrounding element always carries the label.
 */
import type { SVGProps } from "react";

import { cx } from "@/lib/format";

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, className, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
      /* Merged, not replaced: a caller passing `text-[15px]` must not drop the
         size rule, or the SVG expands to fill its container. */
      className={cx("size-[1em] shrink-0", className)}
    >
      {children}
    </svg>
  );
}

export const IconRadar = (p: IconProps) => (
  <Icon {...p}>
    <path d="M19.07 4.93A10 10 0 1 1 4.93 19.07" />
    <path d="M15.54 8.46a5 5 0 1 0-7.08 7.08" />
    <path d="M12 12 21 3" />
  </Icon>
);
export const IconGrid = (p: IconProps) => (
  <Icon {...p}>
    <rect x="3" y="3" width="7" height="7" rx="1.5" />
    <rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" />
    <rect x="14" y="14" width="7" height="7" rx="1.5" />
  </Icon>
);
export const IconAward = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="8" r="5" />
    <path d="M8.5 12.5 7 22l5-3 5 3-1.5-9.5" />
  </Icon>
);
export const IconBriefcase = (p: IconProps) => (
  <Icon {...p}>
    <rect x="2" y="7" width="20" height="14" rx="2" />
    <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </Icon>
);
export const IconTrophy = (p: IconProps) => (
  <Icon {...p}>
    <path d="M6 4h12v5a6 6 0 0 1-12 0z" />
    <path d="M6 6H3v1a4 4 0 0 0 3 3.87M18 6h3v1a4 4 0 0 1-3 3.87" />
    <path d="M9 21h6M12 15v6" />
  </Icon>
);
export const IconUsers = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="9" cy="8" r="3.5" />
    <path d="M2.5 20a6.5 6.5 0 0 1 13 0" />
    <path d="M16 5.2a3.5 3.5 0 0 1 0 6.6M17.5 20a6.5 6.5 0 0 0-2-4.7" />
  </Icon>
);
export const IconSparkles = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6z" />
    <path d="M18 15l.8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8z" />
  </Icon>
);
export const IconGraduationCap = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 4 2 9l10 5 10-5z" />
    <path d="M6 11.5V17c0 1.7 2.7 3 6 3s6-1.3 6-3v-5.5" />
  </Icon>
);
export const IconBookmark = (p: IconProps) => (
  <Icon {...p}>
    <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z" />
  </Icon>
);
export const IconClock = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </Icon>
);
export const IconUser = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 20a8 8 0 0 1 16 0" />
  </Icon>
);
export const IconShield = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 3l8 3v6c0 4.5-3.2 8.3-8 9.5C7.2 20.3 4 16.5 4 12V6z" />
  </Icon>
);
export const IconCheck = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 12.5 9 17.5 20 6.5" />
  </Icon>
);
export const IconX = (p: IconProps) => (
  <Icon {...p}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Icon>
);
export const IconSearch = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-3.5-3.5" />
  </Icon>
);
export const IconFilter = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3 5h18l-7 8v6l-4 2v-8z" />
  </Icon>
);
export const IconArrowRight = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 12h15M13 6l6 6-6 6" />
  </Icon>
);
export const IconExternal = (p: IconProps) => (
  <Icon {...p}>
    <path d="M14 4h6v6" />
    <path d="M20 4 11 13" />
    <path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
  </Icon>
);
export const IconGlobe = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3C9.5 5.7 9.5 18.3 12 21" />
  </Icon>
);
export const IconPin = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11z" />
    <circle cx="12" cy="10" r="2.5" />
  </Icon>
);
export const IconSun = (p: IconProps) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
  </Icon>
);
export const IconMoon = (p: IconProps) => (
  <Icon {...p}>
    <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" />
  </Icon>
);
export const IconMenu = (p: IconProps) => (
  <Icon {...p}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </Icon>
);
export const IconInbox = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3 13h5l1.5 3h5L16 13h5" />
    <path d="M5.4 4.5h13.2l2.4 8.5v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-6z" />
  </Icon>
);
export const IconAlert = (p: IconProps) => (
  <Icon {...p}>
    <path d="M12 3.5 21.5 20h-19z" />
    <path d="M12 10v4M12 17.2v.1" />
  </Icon>
);
export const IconDatabase = (p: IconProps) => (
  <Icon {...p}>
    <ellipse cx="12" cy="6" rx="8" ry="3" />
    <path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6" />
    <path d="M20 12c0 1.7-3.6 3-8 3s-8-1.3-8-3" />
  </Icon>
);
export const IconBolt = (p: IconProps) => (
  <Icon {...p}>
    <path d="M13 2 4 14h7l-1 8 9-12h-7z" />
  </Icon>
);
