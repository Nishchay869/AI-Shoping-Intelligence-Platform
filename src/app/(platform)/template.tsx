/** Next.js remounts `template` (unlike `layout`) on every navigation, so the CSS
 * entrance animation replays per route change without any client-side JS/state. */
export default function PlatformTemplate({ children }: { children: React.ReactNode }) {
  return <div className="page-enter">{children}</div>;
}
