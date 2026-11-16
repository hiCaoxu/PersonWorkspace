import animate from 'tailwindcss-animate'
import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: { DEFAULT: '#FAF7F2', card: '#FFFFFF', sunken: '#F5F1E8' },
        ink: { DEFAULT: '#3D3528', muted: '#8A7F70', faint: '#B4A99A' },
        clay: {
          50: '#FBF6F0',
          100: '#F3E9DE',
          200: '#E7D6C3',
          300: '#D9C3A9',
          400: '#C79E7E',
          500: '#B08968',
          600: '#9A7355',
          700: '#7F5539',
          800: '#654330',
          900: '#4A3123',
        },
        line: { DEFAULT: '#E8E1D5', strong: '#D8CDBC' },
        positive: '#7A9E7E',
        negative: '#C0714F',
      },
      fontFamily: {
        sans: [
          '"Source Han Sans SC"',
          '"Noto Sans SC"',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          'system-ui',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', '"SFMono-Regular"', 'Consolas', 'monospace'],
      },
      fontSize: {
        display: ['28px', { lineHeight: '1.3', fontWeight: '600' }],
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
      boxShadow: {
        soft: '0 1px 2px rgba(61,53,40,0.04)',
        lift: '0 6px 20px -8px rgba(61,53,40,0.16)',
        pop: '0 16px 48px -16px rgba(61,53,40,0.24)',
        inset: 'inset 0 1px 0 rgba(255,255,255,0.6)',
      },
      transitionTimingFunction: {
        calm: 'cubic-bezier(0.22, 0.61, 0.36, 1)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.97)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      animation: {
        'fade-up': 'fade-up 180ms cubic-bezier(0.22, 0.61, 0.36, 1) both',
        'scale-in': 'scale-in 200ms cubic-bezier(0.22, 0.61, 0.36, 1) both',
        'slide-in-right': 'slide-in-right 220ms cubic-bezier(0.22, 0.61, 0.36, 1) both',
        shimmer: 'shimmer 1.4s linear infinite',
      },
    },
  },
  plugins: [animate],
} satisfies Config
