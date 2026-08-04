import type { SVGProps } from "react";

export type IconName =
  | "home" | "search" | "heart" | "message" | "user" | "bell" | "menu" | "arrow" | "sparkles" | "trend"
  | "x" | "mic" | "receipt" | "logout" | "send" | "restart" | "check" | "quote"
  | "cpu" | "bag" | "gift" | "shield" | "clock" | "mail"
  | "social-x" | "social-linkedin" | "social-instagram" | "social-facebook";

const paths: Record<IconName, string> = {
  home: "M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V10.5Z",
  search: "m21 21-4.35-4.35M19 10a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  heart: "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78Z",
  message: "M21 11.5a8.38 8.38 0 0 1-9 8.5 9.7 9.7 0 0 1-4-.9L3 21l1.8-4A8.4 8.4 0 1 1 21 11.5Z",
  user: "M20 21a8 8 0 0 0-16 0m12-14a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-8 13h4",
  menu: "M4 6h16M4 12h16M4 18h16",
  arrow: "m9 18 6-6-6-6",
  sparkles: "m12 3-1.9 5.1L5 10l5.1 1.9L12 17l1.9-5.1L19 10l-5.1-1.9L12 3ZM5 17l-.7 1.8L2.5 19.5l1.8.7L5 22l.7-1.8 1.8-.7-1.8-.7L5 17Z",
  trend: "M3 17 9 11l4 4 8-9M15 6h6v6",
  x: "M6 6l12 12M18 6 6 18",
  mic: "M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3ZM19 10v1a7 7 0 0 1-14 0v-1M12 19v3M8 22h8",
  receipt: "M6 2h12v18l-2-1-2 1-2-1-2 1-2-1-2 1V2ZM9 7h6M9 10.5h6M9 14h4",
  logout: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9",
  send: "M3 12 21 3 14 21 11 13 3 12Z",
  restart: "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8 M3 3v5h5",
  check: "m4 12 5 5L20 6",
  quote: "M7 8a3 3 0 0 0-3 3v2a3 3 0 0 0 3 3h1v3H5m11-11a3 3 0 0 0-3 3v2a3 3 0 0 0 3 3h1v3h-3",
  // Use-case / feature icons
  cpu: "M7 7h10v10H7V7Z M9 7V3M15 7V3M9 21v-4M15 21v-4M7 9H3M7 15H3M21 9h-4M21 15h-4",
  bag: "M5 8h14l-1.5 13h-11L5 8Z M8 8V6a4 4 0 0 1 8 0v2",
  gift: "M4 8h16v4H4V8Z M5 12h14v9H5v-9Z M12 8v13M5 16h14",
  shield: "M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z M9 12l2 2 4-4",
  clock: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z M12 7v5l3.5 2",
  mail: "M2 5h20v14H2V5Z M2 5l10 8 10-8",
  // Social glyphs, redrawn as simple generic pictograms (not brand asset reproductions)
  "social-x": "M5 5l14 14M19 5 5 19",
  "social-linkedin": "M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6Z M2 9h4v12H2V9Z M2 4a2 2 0 1 0 4 0 2 2 0 0 0-4 0Z",
  "social-instagram": "M3 3h18v18H3V3Z M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z M17 7v.01",
  "social-facebook": "M4 4h16v16H4V4Z M14 20v-7h3l.5-3H14V8a1 1 0 0 1 1-1h2.5V4H15a4 4 0 0 0-4 4v3H9v3h2v7"
};

export function Icon({ name, className = "", ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true" {...props}>
      <path d={paths[name]} />
    </svg>
  );
}
