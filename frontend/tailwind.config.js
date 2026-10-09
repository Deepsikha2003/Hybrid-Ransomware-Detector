export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {
    colors: { bg: 'var(--bg)', fg: 'var(--fg)', muted: 'var(--muted)', card: 'var(--card)', line: 'var(--line)', neon: '#22d3ee', safe: '#22c55e', warn: '#eab308', high: '#f97316', danger: '#ef4444' },
    boxShadow: { neon: '0 0 24px rgba(34,211,238,.25)' },
  } },
}
