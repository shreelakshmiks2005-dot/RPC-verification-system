import { useState } from 'react'
import { verifyProject } from '../api/client'
import ResultCard from '../components/ResultCard'

const DEMO_PRESETS = [
  {
    label: '✅ Strong contributor',
    data: { candidate_id: 'demo_01', candidate_name: 'Linus Torvalds', github_username: 'torvalds', repo_link: 'https://github.com/torvalds/uemacs', project_type: 'individual' },
  },
  {
    label: '⚠ Minimal contribution',
    data: { candidate_id: 'demo_02', candidate_name: 'Octocat', github_username: 'octocat', repo_link: 'https://github.com/octocat/Hello-World', project_type: 'individual' },
  },
]

export default function ProjectVerify() {
  const [form, setForm] = useState({
    candidate_name: '',
    github_username: 'octocat',
    repo_link: 'https://github.com/octocat/Hello-World',
    project_type: 'individual',
  })
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [steps, setSteps] = useState<string[]>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null); setSteps([])
    const stepMsgs = [
      'Fetching repository data…',
      'Analysing commit history…',
      'Running Tier 1 scoring…',
      'Checking plagiarism signals…',
    ]
    let i = 0
    const interval = setInterval(() => {
      if (i < stepMsgs.length) setSteps(s => [...s, stepMsgs[i++]])
      else clearInterval(interval)
    }, 600)
    try {
      const data = await verifyProject({
        ...form,
        candidate_id: `cand_${Date.now()}`,
      })
      clearInterval(interval)
      setSteps(stepMsgs)
      setResult(data)
    } catch (err: any) {
      clearInterval(interval)
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : detail?.message ?? err.message ?? 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">💻 Project Validation Module</h1>
        <p className="text-gray-500 mt-1 text-sm">Validates GitHub repositories by analyzing ownership, commit history, and contribution patterns to detect fake or forked projects. <span className="font-medium text-indigo-600">Weight: w₂ = 50%</span></p>
      </div>

      {/* Two-tier explanation */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-xs text-indigo-800">
          <p className="font-bold mb-1">⚡ Tier 1 — Fast Analysis</p>
          <p>Repository ownership, commit count, contributor list, timing patterns, fork detection</p>
        </div>
        <div className="bg-purple-50 border border-purple-100 rounded-xl p-3 text-xs text-purple-800">
          <p className="font-bold mb-1">🔍 Tier 2 — Deep Analysis</p>
          <p>Runs only if Tier 1 score &lt; 75. Plagiarism detection, bulk upload check, tutorial fork detection</p>
        </div>
      </div>
      <div className="flex gap-2 mb-4">
        <span className="text-xs text-gray-400 self-center">Demo presets:</span>
        {DEMO_PRESETS.map(p => (
          <button
            key={p.label}
            type="button"
            onClick={() => setForm(p.data)}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 text-gray-600 hover:text-indigo-700 transition-all"
          >
            {p.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 shadow-sm">
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Candidate Name</label>
          <input required className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-gray-50 focus:bg-white transition" value={form.candidate_name} onChange={set('candidate_name')} placeholder="Jane Doe" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">GitHub Username</label>
          <input required className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-gray-50 focus:bg-white transition" value={form.github_username} onChange={set('github_username')} placeholder="johndoe" />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Repository URL</label>
          <input
            required
            type="url"
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-gray-50 focus:bg-white transition"
            value={form.repo_link}
            onChange={e => {
              // Auto-strip .git suffix that GitHub clone URLs include
              let val = e.target.value.trim()
              if (val.endsWith('.git')) val = val.slice(0, -4)
              setForm(f => ({ ...f, repo_link: val }))
            }}
            placeholder="https://github.com/username/repo"
          />
          <p className="text-xs text-gray-400 mt-1">Paste any GitHub URL — clone URLs with .git are handled automatically</p>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Project Type</label>
          <select className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-gray-50 focus:bg-white transition" value={form.project_type} onChange={set('project_type')}>
            <option value="individual">Individual</option>
            <option value="group">Group / Team</option>
          </select>
        </div>

        {/* Loading steps */}
        {loading && steps.length > 0 && (
          <div className="bg-indigo-50 rounded-xl p-4 space-y-1.5">
            {steps.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-indigo-700">
                <span className="text-green-500">✓</span> {s}
              </div>
            ))}
            <div className="flex items-center gap-2 text-sm text-indigo-400 animate-pulse">
              <span>⏳</span> Processing…
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 space-y-1.5">
            <p className="text-red-700 text-sm font-semibold">❌ Verification Failed</p>
            <p className="text-red-600 text-sm">{error}</p>
            {(error.toLowerCase().includes('private') || error.toLowerCase().includes('not found')) && (
              <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
                <p className="font-semibold mb-1">🔑 Private Repository?</p>
                <p>Your GitHub token needs the <code className="bg-amber-100 px-1 rounded">repo</code> scope to access private repos.</p>
                <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="underline font-medium mt-1 inline-block">
                  Generate a new token with repo scope →
                </a>
              </div>
            )}
          </div>
        )}

        <button type="submit" disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold py-3 rounded-xl transition-colors text-sm shadow-sm">
          {loading ? 'Analysing…' : '🔍 Verify GitHub Project'}
        </button>
      </form>

      {result && <ResultCard title="Project Verification Result" icon="💻" result={result} />}
    </div>
  )
}
