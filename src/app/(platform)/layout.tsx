import { AppShell } from "@/components/app-shell";
/** Layout applied to every signed-in product experience. */
export default function PlatformLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <AppShell>{children}</AppShell>; }
