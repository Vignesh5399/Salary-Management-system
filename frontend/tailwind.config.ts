import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FBFBFA",
        ink: "#16181D",
        muted: "#6B7280",
        rule: "#E4E4E7",
        under: "#B4443A",
        over: "#1F6F5C",
      },
      fontFamily: {
        sans: ["var(--font-text)", "system-ui", "sans-serif"],
        figure: ["var(--font-figure)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
