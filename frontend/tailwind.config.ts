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
        background: "#F6F7F9",
        surface: {
          DEFAULT: "#FFFFFF",
          hover: "#F9FAFB",
          active: "#F3F4F6",
          subtle: "#F9FAFB",
        },
        border: {
          DEFAULT: "#E5E7EB",
          subtle: "#F1F5F9",
          bright: "#D1D5DB",
        },
        primary: {
          DEFAULT: "#4F46E5",
          50: "#EEF2FF",
          100: "#E0E7FF",
          600: "#4F46E5",
          700: "#4338CA",
        },
        status: {
          healthy: "#059669",
          degraded: "#D97706",
          critical: "#DC2626",
          info: "#2563EB",
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
