import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border) / <alpha-value>)',
        background: 'hsl(var(--background) / <alpha-value>)',
        foreground: 'hsl(var(--foreground) / <alpha-value>)',
        muted: 'hsl(var(--muted) / <alpha-value>)',
        'muted-foreground': 'hsl(var(--muted-foreground) / <alpha-value>)',
        accent: 'hsl(var(--accent) / <alpha-value>)',
        'accent-foreground': 'hsl(var(--accent-foreground) / <alpha-value>)',
        'entity-paper': 'hsl(var(--entity-paper) / <alpha-value>)',
        'entity-concept': 'hsl(var(--entity-concept) / <alpha-value>)',
        'entity-project': 'hsl(var(--entity-project) / <alpha-value>)',
        'entity-brainstorm': 'hsl(var(--entity-brainstorm) / <alpha-value>)',
        'entity-note': 'hsl(var(--entity-note) / <alpha-value>)',
        'entity-review': 'hsl(var(--entity-review) / <alpha-value>)'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      },
      boxShadow: {
        panel: '0 1px 0 rgba(255, 255, 255, 0.04) inset'
      }
    }
  },
  plugins: []
};

export default config;
