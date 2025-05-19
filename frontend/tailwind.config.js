/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        retro: ['"Press Start 2P"', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: 'var(--primary)',
        secondary: 'var(--secondary)',
        accent: 'var(--accent)',
        background: 'var(--background)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite',
        'scanline': 'scanline 8s linear infinite',
        'pixelate': 'pixelate 3s infinite',
      },
    },
  },
  plugins: [],
} 