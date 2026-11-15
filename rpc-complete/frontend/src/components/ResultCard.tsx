import ScoreGauge from './ScoreGauge'
import FlagList from './FlagList'
import DetailsTable from './DetailsTable'

interface Props { title: string; icon?: string; result: Record<string, unknown> }

export default function ResultCard({ title, icon = '', result }: Props) {
  const tierBadge = result.tier2_complete !== undefined && (
    <div className="flex gap-2 mt-3">
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${result.tier1_complete ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
        Tier 1 {result.tier1_complete ? '✓' : '—'}
      </span>
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
        result.tier2_status === 'not_required' ? 'bg-blue-100 text-blue-700' :
        result.tier2_complete ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
      }`}>
        Tier 2 {result.tier2_status === 'not_required' ? 'skipped' : result.tier2_complete ? '✓' : '—'}
      </span>
    </div>
  )

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mt-6 animate-fade-up">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-bold text-gray-900">{icon} {title}</h2>
        {result.verification_id && (
          <span className="text-xs text-gray-400 font-mono">{String(result.verification_id)}</span>
        )}
      </div>

      {result.score !== undefined && (
        <>
          <ScoreGauge score={result.score as number} status={result.status as string} />
          {tierBadge}
        </>
      )}

      {result.flags && <FlagList flags={result.flags as any[]} />}

      {result.details && typeof result.details === 'object' && !Array.isArray(result.details) && (
        <DetailsTable details={result.details as Record<string, unknown>} />
      )}
      {result.extracted_data && typeof result.extracted_data === 'object' && (
        <DetailsTable details={result.extracted_data as Record<string, unknown>} title="Extracted Data" />
      )}
      {result.skill_analysis && typeof result.skill_analysis === 'object' && (
        <DetailsTable details={result.skill_analysis as Record<string, unknown>} title="Skill Analysis" />
      )}
    </div>
  )
}
