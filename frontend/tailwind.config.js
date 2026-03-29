/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
    "./hooks/**/*.{js,jsx}",
    "./lib/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          950: "#08090d",
          900: "#0f1118",
          800: "#171b24",
          700: "#1f2430",
        },
        accent: {
          300: "#fdb57b",
          400: "#f9944a",
          500: "#f07c2a",
          600: "#d9651f",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(249, 148, 74, 0.18), 0 18px 48px rgba(230, 102, 34, 0.22)",
        card: "0 0 0 1px rgba(255, 255, 255, 0.06), 0 22px 50px rgba(0, 0, 0, 0.35)",
      },
      borderRadius: {
        xl2: "1.35rem",
      },
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "radial-warm": "radial-gradient(circle at 15% 10%, rgba(249, 148, 74, 0.22), transparent 40%), radial-gradient(circle at 88% 16%, rgba(240, 124, 42, 0.14), transparent 38%), linear-gradient(180deg, #090b11 0%, #0d1119 42%, #0a0e14 100%)",
      },
    },
  },
  plugins: [],
};
