import { useState } from 'react'
import { verifyCertificate } from '../api/client'
import ResultCard from '../components/ResultCard'

export default function CertificateVerify() {
  const [form, setForm] = useState({
    candidateName: '',
    expectedCourse: 'Machine Learning Specialization',
    verifyOnline: false,
  })
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) { setError('Please upload a certificate file.'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const data = await verifyCertificate(
        `cand_${Date.now()}`,
        form.candidateName,
        form.expectedCourse,
        form.verifyOnline,
        file,
      )
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
        <h1 className="text-2xl font-bold text-gray-900">🎓 Certificate Authentication Module</h1>
        <p className="text-gray-500 mt-1 text-sm">Verifies certificates using Tesseract OCR for text extraction and QR code scanning to cross-check with official sources. <span className="font-medium text-purple-600">Weight: w₃ = 20%</span></p>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-xl px-4 py-3 mb-4 text-sm text-purple-700">
        <strong>Tip:</strong> Upload any certificate image (PNG/JPG) or PDF. The system reads text via OCR and decodes QR codes automatically.
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4 shadow-sm">
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Candidate Name</label>
          <input required className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 bg-gray-50 focus:bg-white transition" value={form.candidateName} onChange={e => setForm(f => ({ ...f, candidateName: e.target.value }))} />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Expected Course Name</label>
          <input className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 bg-gray-50 focus:bg-white transition" value={form.expectedCourse} onChange={e => setForm(f => ({ ...f, expectedCourse: e.target.value }))} placeholder="e.g. Machine Learning Specialization" />
        </div>

        <label className="flex items-center gap-3 cursor-pointer">
          <div className={`w-10 h-5 rounded-full transition-colors relative ${form.verifyOnline ? 'bg-purple-500' : 'bg-gray-200'}`} onClick={() => setForm(f => ({ ...f, verifyOnline: !f.verifyOnline }))}>
            <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.verifyOnline ? 'translate-x-5' : 'translate-x-0.5'}`} />
          </div>
          <span className="text-sm text-gray-700">Verify online (follows QR / verification URL)</span>
        </label>

        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Certificate File</label>
          <label
            htmlFor="cert-file"
            className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6 cursor-pointer transition-all ${
              file ? 'border-purple-400 bg-purple-50' : 'border-gray-200 bg-gray-50 hover:border-purple-300 hover:bg-purple-50/50'
            }`}
          >
            <input type="file" id="cert-file" accept=".pdf,.png,.jpg,.jpeg,.webp" className="hidden" onChange={e => setFile(e.target.files?.[0] ?? null)} />
            {file ? (
              <>
                <span className="text-3xl mb-2">🎓</span>
                <span className="text-sm font-semibold text-purple-700">{file.name}</span>
                <span className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(1)} KB — click to change</span>
              </>
            ) : (
              <>
                <span className="text-3xl mb-2">⬆</span>
                <span className="text-sm font-semibold text-gray-600">Click to upload certificate</span>
                <span className="text-xs text-gray-400 mt-1">PDF, PNG, JPG, or WEBP</span>
              </>
            )}
          </label>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <button type="submit" disabled={loading} className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white font-semibold py-3 rounded-xl transition-colors text-sm shadow-sm">
          {loading ? '⏳ Verifying certificate…' : '🔍 Verify Certificate'}
        </button>
      </form>

      {result && <ResultCard title="Certificate Verification Result" icon="🎓" result={result} />}
    </div>
  )
}
