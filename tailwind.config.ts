import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0d1c2f",
        // Soft-UI (neumorphic) base surface - everything (nav, cards, buttons, inputs) sits on this
        // same tone so the dual light/dark shadow pair reads as "extruded from the same material."
        surface: "#E8ECF5",
        // Electric Indigo/Violet - standard Tailwind indigo ramp, used as the sole accent on the
        // otherwise-monochrome neumorphic surface (buttons, links, active states, gradients).
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81"
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"]
      },
      boxShadow: {
        card: "0 8px 24px rgba(13, 28, 47, 0.06)",
        "card-hover": "0 20px 40px -8px rgba(13, 28, 47, 0.14)",
        "glow-brand": "0 0 0 1px rgba(79, 70, 229, 0.08), 0 8px 24px -4px rgba(79, 70, 229, 0.3)",
        // Neumorphic (soft-UI) shadow pairs: dark shadow bottom-right, light shadow top-left, on the
        // `surface` base color. "neu" = resting/raised, "neu-inset" = pressed/concave (inputs, active nav).
        "neu-sm": "3px 3px 7px rgba(163, 177, 198, 0.5), -3px -3px 7px rgba(255, 255, 255, 0.75)",
        neu: "6px 6px 14px rgba(163, 177, 198, 0.5), -6px -6px 14px rgba(255, 255, 255, 0.8)",
        "neu-lg": "12px 12px 28px rgba(163, 177, 198, 0.5), -12px -12px 28px rgba(255, 255, 255, 0.8)",
        "neu-inset-sm": "inset 2px 2px 5px rgba(163, 177, 198, 0.5), inset -2px -2px 5px rgba(255, 255, 255, 0.75)",
        "neu-inset": "inset 4px 4px 9px rgba(163, 177, 198, 0.55), inset -4px -4px 9px rgba(255, 255, 255, 0.8)",
        "neu-inset-lg": "inset 7px 7px 16px rgba(163, 177, 198, 0.55), inset -7px -7px 16px rgba(255, 255, 255, 0.8)",
        "neu-brand": "6px 6px 16px rgba(79, 70, 229, 0.35), -4px -4px 12px rgba(255, 255, 255, 0.7)",
        "neu-brand-inset": "inset 3px 3px 8px rgba(55, 48, 163, 0.55), inset -3px -3px 8px rgba(129, 140, 248, 0.35)"
      },
      backdropBlur: { xs: "2px" },
      keyframes: {
        "fade-slide-up": { "0%": { opacity: "0", transform: "translateY(10px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "fade-out": { "0%": { opacity: "1" }, "100%": { opacity: "0" } },
        "scale-in": { "0%": { opacity: "0", transform: "scale(0.94)" }, "100%": { opacity: "1", transform: "scale(1)" } },
        "scale-out": { "0%": { opacity: "1", transform: "scale(1)" }, "100%": { opacity: "0", transform: "scale(0.94)" } },
        "drawer-in": { "0%": { opacity: "0", transform: "translateX(-16px)" }, "100%": { opacity: "1", transform: "translateX(0)" } },
        "drawer-out": { "0%": { opacity: "1", transform: "translateX(0)" }, "100%": { opacity: "0", transform: "translateX(-16px)" } },
        "float-slow": { "0%, 100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-10px)" } },
        "nav-in": { "0%": { opacity: "0", transform: "translateY(-18px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        "mark-highlight": { "0%": { backgroundSize: "0% 0.85em" }, "100%": { backgroundSize: "100% 0.85em" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } }
      },
      animation: {
        "fade-slide-up": "fade-slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in": "fade-in 0.4s ease-out both",
        "fade-out": "fade-out 0.2s ease-in both",
        "scale-in": "scale-in 0.25s cubic-bezier(0.16, 1, 0.3, 1) both",
        "scale-out": "scale-out 0.18s ease-in both",
        "drawer-in": "drawer-in 0.28s cubic-bezier(0.16, 1, 0.3, 1) both",
        "drawer-out": "drawer-out 0.2s ease-in both",
        "float-slow": "float-slow 6s ease-in-out infinite",
        "nav-in": "nav-in 0.7s cubic-bezier(0.16, 1, 0.3, 1) both",
        "mark-highlight": "mark-highlight 1s cubic-bezier(0.65, 0, 0.35, 1) 0.7s both",
        shimmer: "shimmer 2.5s linear infinite",
        marquee: "marquee 32s linear infinite"
      }
    }
  },
  plugins: []
} satisfies Config;
