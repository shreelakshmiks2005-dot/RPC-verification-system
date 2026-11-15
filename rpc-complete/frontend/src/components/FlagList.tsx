interface Flag { type: string; code: string; message: string }
interface Props { flags: Flag[] }

const cfg: Record<string, { bar: string; bg: string; text: string; icon: string }> = {
  positive: { bar: 'bg-green-500',  bg: 'bg-green-50',  text: 'text-green-800',  icon: '✓' },
  warning:  { bar: 'bg-yellow-400', bg: 'bg-yellow-50', text: 'text-yellow-800', icon: '⚠' },
  negative: { bar: 'bg-red-500',    bg: 'bg-red-50',    text: 'text-red-800',    icon: '✗' },
}

export default function FlagList({ flags }: Props) {
  if (!flags?.length) return null
  const pos = flags.filter(f => f.type === 'positive')
  const neg = flags.filter(f => f.type !== 'positive')

  return (
    <div className="mt-5 space-y-3">
      {neg.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Issues Found</p>
          <div className="space-y-1.5">
            {neg.map((f, i) => {
              const c = cfg[f.type] ?? cfg.warning
              return (
                <div key={i} className={`flex items-start gap-3 px-3 py-2.5 rounded-xl ${c.bg}`}>
                  <span className={`text-sm font-bold mt-0.5 ${c.text}`}>{c.icon}</span>
                  <div className={`text-sm ${c.text}`}>
                    <span className="font-mono text-xs opacity-60 mr-1.5">{f.code}</span>
                    {f.message}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
      {pos.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">Positive Signals</p>
          <div className="flex flex-wrap gap-2">
            {pos.map((f, i) => (
              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1 bg-green-50 rounded-full text-xs text-green-700 font-medium">
                <span>✓</span>
                <span>{f.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
