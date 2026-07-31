import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0d1c2f",
        // Anchored on Stitch's "Deep Emerald" (#1f7a5c) design system - see analytical_intelligence/DESIGN.md.
        brand: {
          50: "#eafbf4",
          100: "#cdf3e3",
          200: "#9ee7cc",
          300: "#82d7b3",
          400: "#4bb98f",
          500: "#2e8f6b",
          600: "#1f7a5c",
          700: "#006046",
          800: "#00513a",
          900: "#002115"
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"]
      },
      boxShadow: { card: "0 8px 24px rgba(13, 28, 47, 0.06)" }
    }
  },
  plugins: []
} satisfies Config;
