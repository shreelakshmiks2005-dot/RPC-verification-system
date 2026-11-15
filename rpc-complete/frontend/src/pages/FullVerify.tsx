import { useState } from 'react'
import { verifyFull } from '../api/client'
import ScoreGauge from '../components/ScoreGauge'
import FlagList from '../components/FlagList'
import ResultCard from '../components/ResultCard'

export default function FullVerify() {
  const [form, setForm] = useState({
    candidate_id: `full_${Date.now()}`,
    candidate_name: '',
    github_username: '',
    repo_link: '',
    project_type: 'individual',
    required_skills: 'python, react, sql',
    preferred_skills: 'docker, aws',
    expected_course: '',
    verify_online: false,
  })
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [certFile, setCertFile] = useState<File | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [steps, setSteps] = useState<string[]>([])

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null); setSteps([])
    const stepMsgs = ['Verifying resume…', 'Analysing GitHub project…', 'Checking certificate…', 'Calculating trust score…']
    let i = 0
    const interval = setInterval(() => {
      if (i < stepMsgs.length) setSteps(s => [...s, stepMsgs[i++]])
      else clearInterval(interval)
    }, 1200)
    try {
      const data = await verifyFull(form, resumeFile, certFile)
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

  const ic = 'w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400 bg-gray-50 focus:bg-white transition'
  const lc = 'block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1'

  const riskColors: Record<string, string> = {
    low: 'text-green-700 bg-green-50 border-green-200',
    medium: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    high: 'text-orange-700 bg-orange-50 border-orange-200',
    critical: 'text-red-700 bg-red-50 border-red-200',
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">⚖ Trust Score Engine</h1>
        <p className="text-gray-500 mt-1 text-sm">Runs all three modules in parallel and combines outputs using the weighted formula <span className="font-mono font-bold text-indigo-700">T = w₁R + w₂P + w₃C</span> to generate a final verification report.</p>
      </div>

      {/* Formula display */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl px-5 py-3 mb-5 text-sm text-indigo-800 text-center">
        <span className="font-mono font-bold text-lg">T = 0.3R + 0.5P + 0.2C</span>
        <div className="flex justify-center gap-6 mt-2 text-xs opacity-70">
          <span>R = Resume Score (w₁)</span>
          <span>P = Project Score (w₂)</span>
          <span>C = Certificate Score (w₃)</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-6 shadow-sm">

        {/* Candidate */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-5 h-5 rounded-full bg-gray-800 text-white flex items-center justify-center text-xs font-bold">1</div>
            <p className="text-sm font-bold text-gray-700">Candidate Info</p>
          </div>
          <div>
            <label className={lc}>Full Name</label>
            <input required className={ic} value={form.candidate_name} onChange={set('candidate_name')} placeholder="e.g. Shreelakshmi K S" />
          </div>
        </div>

        {/* Project */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold">2</div>
            <p className="text-sm font-bold text-gray-700">💻 GitHub Project</p>
            <span className="text-xs text-gray-400">(optional)</span>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><label className={lc}>GitHub Username</label><input className={ic} value={form.github_username} onChange={set('github_username')} placeholder="johndoe" /></div>
              <div>
                <label className={lc}>Project Type</label>
                <select className={`${ic} bg-gray-50`} value={form.project_type} onChange={set('project_type')}>
                  <option value="individual">Individual</option>
                  <option value="group">Group</option>
                </select>
              </div>
            </div>
            <div><label className={lc}>Repository URL</label><input className={ic} type="url" value={form.repo_link} onChange={set('repo_link')} placeholder="https://github.com/username/repo" /></div>
          </div>
        </div>

        {/* Resume */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">3</div>
            <p className="text-sm font-bold text-gray-700">📄 Resume</p>
            <span className="text-xs text-gray-400">(optional)</span>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><label className={lc}>Required Skills</label><input className={ic} value={form.required_skills} onChange={set('required_skills')} placeholder="python, react" /></div>
              <div><label className={lc}>Preferred Skills</label><input className={ic} value={form.preferred_skills} onChange={set('preferred_skills')} placeholder="docker, aws" /></div>
            </div>
            <label htmlFor="full-resume" className={`flex items-center gap-3 border-2 border-dashed rounded-xl px-4 py-3 cursor-pointer transition-all ${resumeFile ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-300 bg-gray-50'}`}>
              <span className="text-xl">{resumeFile ? '📄' : '⬆'}</span>
              <span className="text-sm text-gray-600">{resumeFile ? resumeFile.name : 'Upload resume (PDF/DOCX/TXT)'}</span>
              <input type="file" id="full-resume" accept=".pdf,.docx,.txt" className="hidden" onChange={e => setResumeFile(e.target.files?.[0] ?? null)} />
            </label>
          </div>
        </div>

        {/* Certificate */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-5 h-5 rounded-full bg-purple-600 text-white flex items-center justify-center text-xs font-bold">4</div>
            <p className="text-sm font-bold text-gray-700">🎓 Certificate</p>
            <span className="text-xs text-gray-400">(optional)</span>
          </div>
          <div className="space-y-3">
            <div><label className={lc}>Expected Course Name</label><input className={ic} value={form.expected_course} onChange={set('expected_course')} placeholder="Machine Learning Specialization" /></div>
            <label className="flex items-center gap-3 cursor-pointer">
              <div className={`w-10 h-5 rounded-full transition-colors relative ${form.verify_online ? 'bg-purple-500' : 'bg-gray-200'}`} onClick={() => setForm(f => ({ ...f, verify_online: !f.verify_online }))}>
                <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.verify_online ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
              <span className="text-sm text-gray-600">Verify certificate online</span>
            </label>
            <label htmlFor="full-cert" className={`flex items-center gap-3 border-2 border-dashed rounded-xl px-4 py-3 cursor-pointer transition-all ${certFile ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-purple-300 bg-gray-50'}`}>
              <span className="text-xl">{certFile ? '🎓' : '⬆'}</span>
              <span className="text-sm text-gray-600">{certFile ? certFile.name : 'Upload certificate (PDF/PNG/JPG)'}</span>
              <input type="file" id="full-cert" accept=".pdf,.png,.jpg,.jpeg" className="hidden" onChange={e => setCertFile(e.target.files?.[0] ?? null)} />
            </label>
          </div>
        </div>

        {/* Loading steps */}
        {loading && steps.length > 0 && (
          <div className="bg-green-50 border border-green-100 rounded-xl p-4 space-y-2">
            {steps.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-green-700">
                <span className="text-green-500 font-bold">✓</span> {s}
              </div>
            ))}
            <div className="flex items-center gap-2 text-sm text-green-400 animate-pulse">
              <span>⏳</span> Calculating…
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 space-y-1.5">
            <p className="text-red-700 text-sm font-medium">Error</p>
            <p className="text-red-600 text-sm mt-0.5">{error}</p>
            {(error.toLowerCase().includes('private') || error.toLowerCase().includes('not found')) && (
              <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800">
                <p className="font-semibold mb-1">🔑 Private Repository?</p>
                <p>Your GitHub token needs the <code className="bg-amber-100 px-1 rounded">repo</code> scope.</p>
                <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="underline font-medium mt-1 inline-block">Generate token →</a>
              </div>
            )}
          </div>
        )}

        <button type="submit" disabled={loading} className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white font-bold py-3.5 rounded-xl transition-colors shadow-sm text-base">
          {loading ? '⏳ Running full verification…' : '🛡 Run Full Verification'}
        </button>
      </form>

      {/* Full result */}
      {result && (
        <div className="mt-6 space-y-4 animate-fade-up">

          {/* ── TRUST SCORE (main) ── */}
          <div className={`rounded-2xl border-2 p-6 shadow-sm ${
            (result.trust_score as number) >= 75 ? 'bg-green-50 border-green-300' :
            (result.trust_score as number) >= 45 ? 'bg-yellow-50 border-yellow-300' :
            'bg-red-50 border-red-300'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">⚖ Overall Trust Score</h2>
              {result.verification_id && (
                <span className="text-xs text-gray-400 font-mono">{String(result.verification_id)}</span>
              )}
            </div>

            {/* Big score + gauge */}
            <ScoreGauge score={result.trust_score as number} status={result.authenticity_level as string} />

            {/* Formula */}
            {result.module_scores && Array.isArray(result.module_scores) && (
              <div className="mt-4 bg-white/70 rounded-xl px-4 py-2.5 text-xs text-gray-500 font-mono text-center border border-gray-100">
                T = {(result.module_scores as any[]).map((m: any) =>
                  `${(m.weight * 100).toFixed(0)}%×${m.score}`
                ).join(' + ')} = <strong className="text-gray-800">{result.trust_score as number}</strong>
              </div>
            )}

            {/* Risk + Authenticity */}
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className={`rounded-xl border p-3 text-sm ${riskColors[result.risk_level as string] ?? 'bg-gray-50 border-gray-200 text-gray-700'}`}>
                <div className="text-xs font-semibold uppercase opacity-60 mb-1">Risk Level</div>
                <div className="font-bold capitalize">{String(result.risk_level)}</div>
              </div>
              <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-3 text-sm text-indigo-800">
                <div className="text-xs font-semibold uppercase opacity-60 mb-1">Authenticity</div>
                <div className="font-bold capitalize">{String(result.authenticity_level)}</div>
              </div>
            </div>

            {/* Recommendation */}
            {result.recommendation && (
              <div className={`mt-4 rounded-xl px-4 py-3 text-sm font-medium border ${
                String(result.recommendation).startsWith('APPROVE') ? 'bg-green-100 border-green-200 text-green-800' :
                String(result.recommendation).startsWith('REJECT')  ? 'bg-red-100 border-red-200 text-red-800' :
                'bg-yellow-50 border-yellow-200 text-yellow-800'
              }`}>
                {String(result.recommendation)}
              </div>
            )}

            {/* Risk indicators */}
            {result.risk_indicators && Array.isArray(result.risk_indicators) && (result.risk_indicators as any[]).length > 0 && (
              <div className="mt-4 space-y-1.5">
                {(result.risk_indicators as any[]).map((r: any, i: number) => (
                  <div key={i} className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-xl px-3 py-2">
                    <span className="font-mono text-xs opacity-60 mr-1.5">{r.code}</span>{r.message}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── THREE MODULE SCORE CARDS ── */}
          <div className="grid grid-cols-3 gap-4">

            {/* Resume Score */}
            <div className={`rounded-2xl border-2 p-5 text-center shadow-sm ${
              result.resume_result
                ? (result.resume_result as any).score >= 75 ? 'border-blue-200 bg-blue-50'
                : (result.resume_result as any).score >= 45 ? 'border-yellow-200 bg-yellow-50'
                : 'border-red-200 bg-red-50'
                : 'border-gray-100 bg-gray-50'
            }`}>
              <div className="text-2xl mb-2">📄</div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Resume Score</div>
              {result.resume_result ? (
                <>
                  <div className={`text-5xl font-extrabold mb-1 ${
                    (result.resume_result as any).score >= 75 ? 'text-blue-600' :
                    (result.resume_result as any).score >= 45 ? 'text-yellow-600' : 'text-red-600'
                  }`}>{(result.resume_result as any).score}</div>
                  <div className="text-xs text-gray-400 mb-2">/ 100</div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    (result.resume_result as any).status === 'verified' ? 'bg-green-100 text-green-700' :
                    (result.resume_result as any).status === 'needs_review' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>{(result.resume_result as any).status?.replace('_', ' ')}</span>
                  <div className="text-xs text-gray-400 mt-2">weight: 30%</div>
                </>
              ) : (
                <div className="text-gray-400 text-sm mt-2">Not submitted</div>
              )}
            </div>

            {/* Project Score */}
            <div className={`rounded-2xl border-2 p-5 text-center shadow-sm ${
              result.project_result
                ? (result.project_result as any).score >= 75 ? 'border-indigo-200 bg-indigo-50'
                : (result.project_result as any).score >= 45 ? 'border-yellow-200 bg-yellow-50'
                : 'border-red-200 bg-red-50'
                : 'border-gray-100 bg-gray-50'
            }`}>
              <div className="text-2xl mb-2">💻</div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Project Score</div>
              {result.project_result ? (
                <>
                  <div className={`text-5xl font-extrabold mb-1 ${
                    (result.project_result as any).score >= 75 ? 'text-indigo-600' :
                    (result.project_result as any).score >= 45 ? 'text-yellow-600' : 'text-red-600'
                  }`}>{(result.project_result as any).score}</div>
                  <div className="text-xs text-gray-400 mb-2">/ 100</div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    (result.project_result as any).status === 'verified' ? 'bg-green-100 text-green-700' :
                    (result.project_result as any).status === 'needs_review' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>{(result.project_result as any).status?.replace('_', ' ')}</span>
                  <div className="text-xs text-gray-400 mt-2">weight: 50%</div>
                </>
              ) : (
                <div className="text-gray-400 text-sm mt-2">Not submitted</div>
              )}
            </div>

            {/* Certificate Score */}
            <div className={`rounded-2xl border-2 p-5 text-center shadow-sm ${
              result.certificate_result
                ? (result.certificate_result as any).score >= 75 ? 'border-purple-200 bg-purple-50'
                : (result.certificate_result as any).score >= 45 ? 'border-yellow-200 bg-yellow-50'
                : 'border-red-200 bg-red-50'
                : 'border-gray-100 bg-gray-50'
            }`}>
              <div className="text-2xl mb-2">🎓</div>
              <div className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Certificate Score</div>
              {result.certificate_result ? (
                <>
                  <div className={`text-5xl font-extrabold mb-1 ${
                    (result.certificate_result as any).score >= 75 ? 'text-purple-600' :
                    (result.certificate_result as any).score >= 45 ? 'text-yellow-600' : 'text-red-600'
                  }`}>{(result.certificate_result as any).score}</div>
                  <div className="text-xs text-gray-400 mb-2">/ 100</div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    (result.certificate_result as any).status === 'verified' ? 'bg-green-100 text-green-700' :
                    (result.certificate_result as any).status === 'needs_review' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>{(result.certificate_result as any).status?.replace('_', ' ')}</span>
                  <div className="text-xs text-gray-400 mt-2">weight: 20%</div>
                </>
              ) : (
                <div className="text-gray-400 text-sm mt-2">Not submitted</div>
              )}
            </div>
          </div>

          {/* ── DETAILED FLAGS PER MODULE ── */}
          {result.resume_result && (result.resume_result as any).score !== undefined && (
            <ResultCard title="Resume Details" icon="📄" result={result.resume_result as Record<string, unknown>} />
          )}
          {result.project_result && (result.project_result as any).score !== undefined && (
            <ResultCard title="Project Details" icon="💻" result={result.project_result as Record<string, unknown>} />
          )}
          {result.certificate_result && (result.certificate_result as any).score !== undefined && (
            <ResultCard title="Certificate Details" icon="🎓" result={result.certificate_result as Record<string, unknown>} />
          )}
        </div>
      )}
    </div>
  )
}
