import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080c14",
        surface: {
          DEFAULT: "#0f1623",
          hover: "#152033",
          active: "#1b2942",
          subtle: "#0b101a",
        },
        border: {
          DEFAULT: "#1e293b",
          subtle: "#162030",
          bright: "#334155",
        },
        status: {
          healthy: "#10b981",
          degraded: "#f59e0b",
          critical: "#ef4444",
          info: "#38bdf8",
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
