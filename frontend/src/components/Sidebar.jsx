import {
  LayoutDashboard, Search, Bitcoin, FileText,
  Eye, Home, Shield, FolderOpen, ChevronRight,
  Radio
} from 'lucide-react'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'osint', label: 'OSINT Profiler', icon: Search },
  { id: 'crypto', label: 'Crypto Tracer', icon: Bitcoin },
  { id: 'fraud', label: 'Case Packager', icon: FileText },
  { id: 'darkweb', label: 'Dark Web Monitor', icon: Eye },
  { id: 'deed', label: 'Deed Fraud Scanner', icon: Home },
  { id: 'reputation', label: 'Reputation Scorer', icon: Shield },
  { id: 'cases', label: 'Case Manager', icon: FolderOpen },
]

export default function Sidebar({ activePage, setActivePage }) {
  return (
    <aside
      className="w-64 flex flex-col border-r"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
        minHeight: '100vh'
      }}
    >
      {/* Logo */}
      <div className="p-6 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.3)' }}
          >
            <Radio size={18} style={{ color: 'var(--accent-cyan)' }} />
          </div>
          <div>
            <div className="font-bold text-sm mono tracking-widest" style={{ color: 'var(--accent-cyan)' }}>
              CYBERINTEL
            </div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
              v1.0 · OPERATIONAL
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {NAV.map(({ id, label, icon: Icon }) => {
          const active = activePage === id
          return (
            <button
              key={id}
              onClick={() => setActivePage(id)}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all text-left group"
              style={{
                background: active ? 'rgba(0,212,255,0.1)' : 'transparent',
                border: active ? '1px solid rgba(0,212,255,0.2)' : '1px solid transparent',
                color: active ? 'var(--accent-cyan)' : 'var(--text-muted)',
              }}
            >
              <Icon size={16} />
              <span className="flex-1 font-medium">{label}</span>
              {active && <ChevronRight size={14} />}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>
        <div
          className="rounded-lg p-3 text-xs"
          style={{ background: 'rgba(0,255,136,0.05)', border: '1px solid rgba(0,255,136,0.15)' }}
        >
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--accent-green)' }} />
            <span className="font-semibold mono" style={{ color: 'var(--accent-green)' }}>SYSTEMS ONLINE</span>
          </div>
          <div style={{ color: 'var(--text-muted)' }}>All modules operational</div>
        </div>
      </div>
    </aside>
  )
}
