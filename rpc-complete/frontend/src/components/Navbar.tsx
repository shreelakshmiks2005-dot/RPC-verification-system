import { Link, useLocation } from 'react-router-dom'

const links = [
  { to: '/',            label: 'Home',            icon: '🏠' },
  { to: '/resume',      label: 'Resume',          icon: '📄' },
  { to: '/project',     label: 'Project',         icon: '💻' },
  { to: '/certificate', label: 'Certificate',     icon: '🎓' },
  { to: '/full',        label: 'Trust Score',     icon: '⚖' },
]

export default function Navbar() {
  const { pathname } = useLocation()
  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white text-xs font-bold shadow">RPC</div>
          <span className="font-bold text-gray-900 text-base">RPC Verification</span>
        </Link>
        <div className="flex gap-1">
          {links.slice(1).map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                pathname === l.to
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <span>{l.icon}</span>
              <span className="hidden sm:inline">{l.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
