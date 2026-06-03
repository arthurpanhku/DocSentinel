import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0b0d10",
        panel: "#111418",
        panel2: "#15191f",
        line: "#252b33",
        muted: "#8b95a1",
        text: "#e6edf3",
        accent: "#79c0ff",
        good: "#3fb950",
        warn: "#d29922",
        bad: "#f85149"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      boxShadow: {
        command: "0 12px 48px rgba(0,0,0,0.35)"
      }
    }
  },
  plugins: []
} satisfies Config;
