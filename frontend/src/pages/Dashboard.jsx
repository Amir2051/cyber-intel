import { useState, useEffect } from 'react'
import { Search, Bitcoin, FileText, Eye, Home, Shield, Activity, TrendingUp, AlertCircle } from 'lucide-react'
import { healthCheck } from '../services/api'

const TOOLS = [
  { icon: Search, label: 'OSINT Profiler', desc: 'Actor dossier from email / username / phone', page: 'osint', color: '#00d4ff' },
  { icon: Bitcoin, label: 'Crypto Tracer', desc: 'Wallet graph + scam address flagging', page: 'crypto', color: '#ffb800' },
  { icon: FileText, label: 'Case Packager', desc: 'IC3 / FBI / Secret Service report bundles', page: 'fraud', color: '#00ff88' },
  { icon: Eye, label: 'Dark Web Monitor', desc: 'Keyword alerts across paste & dark sites', page: 'darkweb', color: '#ff3b3b' },
  { icon: Home, label: 'Deed Fraud Scanner', desc: 'Property transfer anomaly detection', page: 'deed', color: '#a78bfa' },
  { icon: Shield, label: 'Reputation Scorer', desc: 'Phone & email risk scoring (0–100)', page: 'reputation', color: '#fb923c' },
]

const STATS = [
  { label: 'Active Monitors', value: '—', icon: Activity },
  { label: 'Alerts This Week', value: '—', icon: AlertCircle },
  { label: 'Cases Packaged', value: '—', icon: FileText },
  { label: 'Wallets Traced', value: '—', icon: TrendingUp },
]

export default function Dashboard() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    healthCheck()
      .then(d => setStatus(d.status))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold mono tracking-widest" style={{ color: 'var(--text-primary)' }}>
            CYBERINTEL PLATFORM
          </h1>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs mono"
            style={{
              background: status === 'operational' ? 'rgba(0,255,136,0.1)' : 'rgba(255,59,59,0.1)',
              border: `1px solid ${status === 'operational' ? 'rgba(0,255,136,0.3)' : 'rgba(255,59,59,0.3)'}`,
              color: status === 'operational' ? 'var(--accent-green)' : 'var(--accent-red)'
            }}>
            <div className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: status === 'operational' ? 'var(--accent-green)' : 'var(--accent-red)' }} />
            {status ? status.toUpperCase() : 'CONNECTING...'}
          </div>
        </div>
        <p style={{ color: 'var(--text-muted)' }} className="text-sm">
          Private Cyber Threat Intelligence &amp; Victim Advocacy Platform
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {STATS.map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-xl p-4"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <div className="flex items-center justify-between mb-3">
              <Icon size={16} style={{ color: 'var(--text-muted)' }} />
            </div>
            <div className="text-2xl font-bold mono mb-1" style={{ color: 'var(--accent-cyan)' }}>{value}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Tools grid */}
      <div className="text-xs font-bold mono mb-4 tracking-widest" style={{ color: 'var(--accent-cyan)' }}>
        ── INTELLIGENCE MODULES
      </div>
      <div className="grid grid-cols-3 gap-4">
        {TOOLS.map(({ icon: Icon, label, desc, page, color }) => (
          <div
            key={page}
            className="rounded-xl p-5 cursor-pointer transition-all group"
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = color}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ background: `${color}18`, border: `1px solid ${color}40` }}>
                <Icon size={18} style={{ color }} />
              </div>
              <div>
                <div className="font-semibold text-sm mono mb-1" style={{ color: 'var(--text-primary)' }}>{label}</div>
                <div className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>{desc}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* API Key Status */}
      <div className="mt-8 rounded-xl p-5"
        style={{ background: 'rgba(255,184,0,0.05)', border: '1px solid rgba(255,184,0,0.2)' }}>
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle size={14} style={{ color: 'var(--accent-amber)' }} />
          <span className="text-xs font-bold mono" style={{ color: 'var(--accent-amber)' }}>API KEYS PENDING</span>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Configure <span className="mono" style={{ color: 'var(--text-primary)' }}>backend/.env</span> with
          your API keys (Hunter.io, Shodan, Etherscan, TronScan, NumVerify, DeHashed, ATTOM, WhoisXML)
          to activate all intelligence modules.
        </p>
      </div>
    </div>
  )
}
