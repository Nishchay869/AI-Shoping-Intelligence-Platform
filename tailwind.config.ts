import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: { ink: "#0F172A", brand: { 50: "#F0FDFA", 500: "#0FAD8C", 600: "#0A8B70", 700: "#08705C" } },
      boxShadow: { card: "0 8px 24px rgba(15, 23, 42, 0.06)" }
    }
  },
  plugins: []
} satisfies Config;
