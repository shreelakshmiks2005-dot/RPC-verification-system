interface Props { details: Record<string, unknown>; title?: string }

export default function DetailsTable({ details, title = 'Details' }: Props) {
  const entries = Object.entries(details).filter(([, v]) => v !== null && v !== undefined && v !== '')
  if (!entries.length) return null
  return (
    <div className="mt-5">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">{title}</p>
      <div className="rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <tbody>
            {entries.map(([k, v], i) => (
              <tr key={k} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/60'}>
                <td className="px-4 py-2.5 text-gray-500 font-medium w-5/12 capitalize">{k.replace(/_/g, ' ')}</td>
                <td className="px-4 py-2.5 text-gray-800 font-mono text-xs">
                  {Array.isArray(v) ? (v.length ? v.join(', ') : '—') : (String(v) || '—')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
