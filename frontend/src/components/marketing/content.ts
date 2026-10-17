import {
  IconAward,
  IconBriefcase,
  IconGraduationCap,
  IconSparkles,
  IconTrophy,
  IconUsers,
} from "@/components/ui/Icons";

/** Cycled in the headline: "Stop searching for …". */
export const ROTATING = [
  "internships.",
  "hackathons.",
  "certifications.",
  "scholarships.",
  "fellowships.",
  "student perks.",
];

/** Where records come from, as named in the source registry. */
export const SOURCES = [
  "Devpost",
  "Major League Hacking",
  "Unstop",
  "GitHub Education",
  "Microsoft Learn",
  "Google Summer of Code",
  "Outreachy",
  "SimplifyJobs",
  "AWS",
  "Microsoft Azure",
];

export const CATEGORIES = [
  { name: "Internships", icon: IconBriefcase },
  { name: "Hackathons", icon: IconTrophy },
  { name: "Certifications", icon: IconAward },
  { name: "Scholarships", icon: IconGraduationCap },
  { name: "Fellowships", icon: IconUsers },
  { name: "Tech benefits", icon: IconSparkles },
];
