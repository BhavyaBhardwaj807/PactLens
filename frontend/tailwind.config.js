/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "dark-bg": "#0B0F1A",
        "dark-card": "#111827",
        "dark-border": "#1F2937",

        "accent-cyan": "#22D3EE",
        "accent-blue": "#3B82F6",

        "risk-high": "#EF4444",
        "risk-medium": "#F59E0B",
        "risk-low": "#60A5FA",
      },
      boxShadow: {
        accent: "0 0 20px rgba(34, 211, 238, 0.25)",
      },
      backgroundImage: {
        "gradient-accent":
          "linear-gradient(135deg, #22D3EE 0%, #3B82F6 100%)",
      },

      /* 🔴 THIS PART IS MANDATORY */
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out forwards",
      },
    },
  },
  plugins: [],
};
