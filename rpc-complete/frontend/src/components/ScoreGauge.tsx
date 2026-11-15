interface Props {
  score: number
  status: string
  size?: 'sm' | 'lg'
}

const statusConfig: Record<string, { color: string; bg: string; label: string; emoji: string }> = {
  verified:     { color: '#16a34a', bg: 'bg-green-50',  label: 'Verified',     emoji: '✓' },
  needs_review: { color: '#d97706', bg: 'bg-yellow-50', label: 'Needs Review', emoji: '⚠' },
  suspicious:   { color: '#dc2626', bg: 'bg-red-50',    label: 'Suspicious',   emoji: '✗' },
  high:         { color: '#16a34a', bg: 'bg-green-50',  label: 'High',         emoji: '✓' },
  medium:       { color: '#d97706', bg: 'bg-yellow-50', label: 'Medium',       emoji: '~' },
  low:          { color: '#dc2626', bg: 'bg-red-50',    label: 'Low',          emoji: '✗' },
  very_low:     { color: '#7f1d1d', bg: 'bg-red-100',   label: 'Very Low',     emoji: '✗' },
}

export default function ScoreGauge({ score, status, size = 'lg' }: Props) {
  const cfg = statusConfig[status] ?? { color: '#6366f1', bg: 'bg-indigo-50', label: status, emoji: '?' }
  const r = size === 'lg' ? 54 : 36
  const stroke = size === 'lg' ? 10 : 7
  const cx = r + stroke
  const cy = r + stroke
  const circumference = 2 * Math.PI * r
  const pct = Math.min(100, Math.max(0, score)) / 100
  const dash = circumference * pct
  const svgSize = (r + stroke) * 2

  return (
    <div className="flex items-center gap-5">
      <div className="relative animate-count-up">
        <svg width={svgSize} height={svgSize} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e5e7eb" strokeWidth={stroke} />
          <circle
            cx={cx} cy={cy} r={r} fill="none"
            stroke={cfg.color}
            strokeWidth={stroke}
            strokeDasharray={`${dash} ${circumference}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center" style={{ transform: 'rotate(0deg)' }}>
          <span className={`font-bold leading-none ${size === 'lg' ? 'text-3xl' : 'text-xl'}`} style={{ color: cfg.color }}>{score}</span>
          <span className="text-xs text-gray-400">/100</span>
        </div>
      </div>
      <div>
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold ${cfg.bg}`} style={{ color: cfg.color }}>
          <span>{cfg.emoji}</span>
          <span>{cfg.label}</span>
        </div>
        <div className="text-xs text-gray-400 mt-1">Trust Score</div>
      </div>
    </div>
  )
}
