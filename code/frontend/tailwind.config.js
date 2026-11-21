/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: { ink: '#0B0B15' },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'Times New Roman', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      animation: {
        'float-slow': 'float 6s ease-in-out infinite',
        'float-slower': 'float 8s ease-in-out infinite reverse',
        'fade-in-up': 'fadeInUp 0.6s ease-out both',
        'fade-in': 'fadeIn 0.4s ease-out both',
        'slide-in': 'slideIn 0.3s ease-out both',
        blink: 'blink 1s step-end infinite',
        shimmer: 'shimmer 1.8s linear infinite',
        'glow-pulse': 'glowPulse 5s ease-in-out infinite',
      },
      keyframes: {
        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-16px)' } },
        fadeInUp: { '0%': { opacity: '0', transform: 'translateY(14px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideIn: { '0%': { opacity: '0', transform: 'translateX(-8px)' }, '100%': { opacity: '1', transform: 'translateX(0)' } },
        blink: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        glowPulse: { '0%, 100%': { opacity: '0.55' }, '50%': { opacity: '1' } },
      },
    },
  },
  plugins: [],
}
