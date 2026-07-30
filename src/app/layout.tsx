import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pricewise | Shopping Intelligence",
  description: "Track prices and make better buying decisions."
};

/** Root document shell shared by every route. */
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
