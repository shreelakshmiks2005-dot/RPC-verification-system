interface Props {
  score: number
  status: string
}

const statusStyles: Record<string, string> = {
  verified: 'bg-green-100 text-green-800 border-green-300',
  needs_review: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  suspicious: 'bg-red-100 text-red-800 border-red-300',
}

const statusLabel: Record<string, string> = {
  verified: 'Verified ✓',
  needs_review: 'Needs Review ⚠',
  suspicious: 'Suspicious ✗',
}

const scoreColor = (score: number) => {
  if (score >= 75) return 'text-green-600'
  if (score >= 45) return 'text-yellow-600'
  return 'text-red-600'
}

export default function ScoreBadge({ score, status }: Props) {
  return (
    <div className="flex items-center gap-4">
      <div className={`text-5xl font-bold ${scoreColor(score)}`}>{score}</div>
      <div>
        <div className="text-sm text-gray-500 mb-1">Trust Score / 100</div>
        <span className={`px-3 py-1 rounded-full border text-sm font-medium ${statusStyles[status] ?? 'bg-gray-100 text-gray-700 border-gray-300'}`}>
          {statusLabel[status] ?? status}
        </span>
      </div>
    </div>
  )
}
