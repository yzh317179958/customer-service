/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fiido: {
          DEFAULT: '#00a6a0',
          dark: '#008b86',
          light: '#f0f9f9',
          black: '#0f172a',
          slate: '#1e293b'
        }
      },
      fontFamily: {
        brand: ['Inter', 'Noto Sans SC', 'sans-serif'],
        sans: ['Inter', 'Noto Sans SC', 'sans-serif']
      }
    }
  },
  plugins: [],
}
