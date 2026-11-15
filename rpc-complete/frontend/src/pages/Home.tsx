import { Link } from 'react-router-dom'

const modules = [
  {
    to: '/resume',
    icon: '📄',
    title: 'Resume Validation',
    desc: 'Extract skills, contacts, and GitHub links from PDF/DOCX resumes. Match against job requirements using NLP.',
    tag: 'NLP + Skill Matching',
    weight: '30%',
    color: 'bg-blue-600',
    light: 'bg-blue-50 border-blue-100',
    btn: 'bg-blue-600 hover:bg-blue-700',
  },
  {
    to: '/project',
    icon: '💻',
    title: 'Project Validation',
    desc: 'Verify GitHub contributions via commit history, file stats, timing patterns, and plagiarism detection.',
    tag: 'GitHub REST API · 2-Tier',
    weight: '50%',
    color: 'bg-indigo-600',
    light: 'bg-indigo-50 border-indigo-100',
    btn: 'bg-indigo-600 hover:bg-indigo-700',
  },
  {
    to: '/certificate',
    icon: '🎓',
    title: 'Certificate Authentication',
    desc: 'OCR-extract certificate details, decode QR codes, and verify online with the issuing organisation.',
    tag: 'OCR + QR Verification',
    weight: '20%',
    color: 'bg-purple-600',
    light: 'bg-purple-50 border-purple-100',
    btn: 'bg-purple-600 hover:bg-purple-700',
  },
]

const stats = [
  { value: '12+', label: 'Fraud Signals', sub: 'Per verification' },
  { value: '2-Tier', label: 'Project Analysis', sub: 'Deep + Fast checks' },
  { value: '0–100', label: 'Trust Score', sub: 'Weighted formula' },
  { value: '< 10s', label: 'Response Time', sub: 'Per module' },
]

const steps = [
  { icon: '📤', label: 'Submit', desc: 'Resume · GitHub URL · Certificate' },
  { icon: '⚙', label: 'Process', desc: 'NLP · GitHub API · OCR' },
  { icon: '🔍', label: 'Analyse', desc: '12+ fraud signals checked' },
  { icon: '⚖', label: 'Score', desc: 'T = 0.3R + 0.5P + 0.2C' },
  { icon: '📋', label: 'Report', desc: 'Approve · Review · Reject' },
]

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto">

      {/* ── Hero ─────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 px-10 py-16 mb-10 text-white text-center shadow-xl">
        {/* background dots */}
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '28px 28px' }} />

        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm text-white text-xs font-semibold px-4 py-1.5 rounded-full mb-6 border border-white/20">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse inline-block" />
            System Online — All Modules Active
          </div>

          <h1 className="text-5xl font-extrabold mb-4 leading-tight">
            RPC Verification System
          </h1>
          <p className="text-indigo-200 text-lg max-w-2xl mx-auto mb-3 font-medium">
            Resume · Project · Certificate Authentication
          </p>
          <p className="text-indigo-300 text-sm max-w-xl mx-auto mb-10 leading-relaxed">
            Automated multi-layer candidate credential verification.
            Detects fraud across GitHub contributions, resumes, and certificates
            — generating a unified trust score for recruiters.
          </p>

          <div className="flex justify-center gap-4 flex-wrap">
            <Link to="/full"
              className="bg-white text-indigo-700 font-bold px-7 py-3 rounded-xl hover:bg-indigo-50 transition-all shadow-lg text-sm">
              🛡 Full Verification
            </Link>
            <Link to="/project"
              className="bg-indigo-500/50 hover:bg-indigo-500/70 backdrop-blur-sm text-white font-semibold px-7 py-3 rounded-xl border border-white/20 transition-all text-sm">
              💻 Project Check
            </Link>
            <Link to="/resume"
              className="bg-indigo-500/50 hover:bg-indigo-500/70 backdrop-blur-sm text-white font-semibold px-7 py-3 rounded-xl border border-white/20 transition-all text-sm">
              📄 Resume Check
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stats ────────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-4 mb-10">
        {stats.map(s => (
          <div key={s.label} className="bg-white rounded-2xl border border-gray-100 p-5 text-center shadow-sm hover:shadow-md transition-shadow">
            <div className="text-3xl font-extrabold text-indigo-600 mb-1">{s.value}</div>
            <div className="text-sm font-semibold text-gray-800">{s.label}</div>
            <div className="text-xs text-gray-400 mt-0.5">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Trust Score Formula ──────────────────────────── */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-2xl p-6 mb-10 text-center shadow-sm">
        <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-2">Trust Score Formula</p>
        <div className="text-3xl font-extrabold text-indigo-700 font-mono mb-3">T = w₁R + w₂P + w₃C</div>
        <div className="flex justify-center gap-8 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
            <span className="text-gray-600"><strong className="text-blue-600">R</strong> Resume <span className="text-gray-400">(w₁ = 0.30)</span></span>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-indigo-600 inline-block" />
            <span className="text-gray-600"><strong className="text-indigo-600">P</strong> Project <span className="text-gray-400">(w₂ = 0.50)</span></span>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-500 inline-block" />
            <span className="text-gray-600"><strong className="text-purple-600">C</strong> Certificate <span className="text-gray-400">(w₃ = 0.20)</span></span>
          </span>
        </div>
      </div>

      {/* ── Score Legend ─────────────────────────────────── */}
      <div className="flex justify-center gap-8 mb-10">
        {[
          { dot: 'bg-green-500', label: 'Verified', range: '≥ 75' },
          { dot: 'bg-yellow-500', label: 'Needs Review', range: '45 – 74' },
          { dot: 'bg-red-500', label: 'Suspicious', range: '< 45' },
        ].map(l => (
          <div key={l.label} className="flex items-center gap-2 text-sm">
            <span className={`w-3 h-3 rounded-full ${l.dot} inline-block`} />
            <span className="font-medium text-gray-700">{l.label}</span>
            <span className="text-gray-400 text-xs">{l.range}</span>
          </div>
        ))}
      </div>

      {/* ── Module Cards ─────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-5 mb-10">
        {modules.map(m => (
          <Link key={m.to} to={m.to}
            className={`group rounded-2xl border p-6 hover:shadow-lg transition-all block ${m.light}`}>
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 ${m.color} rounded-xl flex items-center justify-center text-2xl shadow-sm`}>
                {m.icon}
              </div>
              <span className="text-xs font-bold text-gray-400 bg-white px-2 py-1 rounded-lg border border-gray-100">
                {m.weight} weight
              </span>
            </div>
            <h2 className="text-base font-bold text-gray-900 mb-2">{m.title}</h2>
            <p className="text-gray-500 text-xs leading-relaxed mb-4">{m.desc}</p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">{m.tag}</span>
              <div className={`px-3 py-1.5 rounded-lg text-white text-xs font-semibold transition-colors ${m.btn}`}>
                Start →
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* ── Full Verification CTA ────────────────────────── */}
      <div className="bg-white border-2 border-indigo-100 rounded-2xl p-6 mb-10 flex items-center justify-between shadow-sm hover:shadow-md transition-shadow">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center text-2xl shadow">
            ⚖
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">Trust Score Engine</h2>
            <p className="text-sm text-gray-500">Run all three modules together — get a combined score, risk level, and recommendation.</p>
          </div>
        </div>
        <Link to="/full"
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold px-6 py-3 rounded-xl transition-all shadow-sm text-sm whitespace-nowrap">
          Run Full Check →
        </Link>
      </div>

      {/* ── How It Works ─────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 text-center mb-8">How It Works</h2>
        <div className="flex items-start justify-between gap-2">
          {steps.map((s, i) => (
            <div key={i} className="flex-1 text-center relative">
              {i < steps.length - 1 && (
                <div className="absolute top-6 left-[60%] w-full h-0.5 bg-gradient-to-r from-indigo-200 to-transparent" />
              )}
              <div className="w-12 h-12 bg-indigo-50 border border-indigo-100 rounded-2xl flex items-center justify-center text-xl mx-auto mb-3 relative z-10">
                {s.icon}
              </div>
              <div className="text-xs font-bold text-indigo-500 uppercase tracking-wide mb-1">{s.label}</div>
              <div className="text-xs text-gray-400 leading-tight">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
