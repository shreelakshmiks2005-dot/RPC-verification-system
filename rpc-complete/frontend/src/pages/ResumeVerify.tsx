import { useState } from 'react'
import { verifyResume } from '../api/client'
import ResultCard from '../components/ResultCard'

export default function ResumeVerify() {
  const [form, setForm] = useState({
    candidateId: 'demo_01',
    candidateName: 'Jane Doe',
    requiredSkills: 'python, react, sql',
    preferredSkills: 'docker, kubernetes, aws',
  })
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) { setError('Please upload a resume file (PDF, DOCX, or TXT).'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await verifyResume(form.candidateId, form.candidateName, form.requiredSkills, form.preferredSkills, file)
      setResult(data)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : detail?.message ?? err.message ?? 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📄 Resume Validation Module</h1>
        <p className="text-gray-500 mt-1 text-sm">Extracts and analyzes skills, project details, and links from resumes using NLP techniques. Structures data into JSON format for scoring. <span className="font-medium text-blue-600">Weight: w₁ = 30%</span></p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 shadow-sm">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Candidate ID</label>
            <input required className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50 focus:bg-white transition" value={form.candidateId} onChange={e => setForm(f => ({ ...f, candidateId: e.target.value }))} placeholder="cand_001" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Candidate Name</label>
            <input required className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50 focus:bg-white transition" value={form.candidateName} onChange={e => setForm(f => ({ ...f, candidateName: e.target.value }))} placeholder="Jane Doe" />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Required Skills</label>
          <input className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50 focus:bg-white transition" value={form.requiredSkills} onChange={e => setForm(f => ({ ...f, requiredSkills: e.target.value }))} placeholder="python, react, sql  (comma separated)" />
          <p className="text-xs text-gray-400 mt-1">Comma separated — e.g. python, react, sql</p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Preferred Skills</label>
          <input className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50 focus:bg-white transition" value={form.preferredSkills} onChange={e => setForm(f => ({ ...f, preferredSkills: e.target.value }))} placeholder="docker, kubernetes, aws" />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Resume File</label>
          <label
            htmlFor="resume-file"
            className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6 cursor-pointer transition-all ${
              file ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-gray-50 hover:border-blue-300 hover:bg-blue-50/50'
            }`}
          >
            <input type="file" id="resume-file" accept=".pdf,.docx,.txt" className="hidden" onChange={e => setFile(e.target.files?.[0] ?? null)} />
            {file ? (
              <>
                <span className="text-3xl mb-2">📄</span>
                <span className="text-sm font-semibold text-blue-700">{file.name}</span>
                <span className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(1)} KB — click to change</span>
              </>
            ) : (
              <>
                <span className="text-3xl mb-2">⬆</span>
                <span className="text-sm font-semibold text-gray-600">Click to upload resume</span>
                <span className="text-xs text-gray-400 mt-1">PDF, DOCX, or TXT</span>
              </>
            )}
          </label>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-3 rounded-xl transition-colors text-sm shadow-sm">
          {loading ? '⏳ Analysing resume…' : '🔍 Verify Resume'}
        </button>
      </form>

      {result && <ResultCard title="Resume Verification Result" icon="📄" result={result} />}
    </div>
  )
}
