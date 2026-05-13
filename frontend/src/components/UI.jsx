import { Loader2, AlertTriangle } from 'lucide-react'

export function PageHeader({ title, subtitle, icon: Icon }) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-2">
        {Icon && (
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.2)' }}
          >
            <Icon size={20} style={{ color: 'var(--accent-cyan)' }} />
          </div>
        )}
        <h1 className="text-2xl font-bold mono tracking-wide" style={{ color: 'var(--text-primary)' }}>
          {title}
        </h1>
      </div>
      {subtitle && (
        <p className="text-sm ml-13" style={{ color: 'var(--text-muted)', marginLeft: Icon ? '52px' : 0 }}>
          {subtitle}
        </p>
      )}
    </div>
  )
}

export function Card({ children, className = '', style = {} }) {
  return (
    <div
      className={`rounded-xl p-5 ${className}`}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        ...style
      }}
    >
      {children}
    </div>
  )
}

export function InputField({ label, value, onChange, placeholder, type = 'text' }) {
  return (
    <div>
      <label className="block text-xs font-medium mb-1.5 mono" style={{ color: 'var(--text-muted)' }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2.5 rounded-lg text-sm outline-none transition-all"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          color: 'var(--text-primary)',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--accent-cyan)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />
    </div>
  )
}

export function SelectField({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs font-medium mb-1.5 mono" style={{ color: 'var(--text-muted)' }}>
        {label}
      </label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2.5 rounded-lg text-sm outline-none"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          color: 'var(--text-primary)',
        }}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

export function TextArea({ label, value, onChange, placeholder, rows = 4 }) {
  return (
    <div>
      <label className="block text-xs font-medium mb-1.5 mono" style={{ color: 'var(--text-muted)' }}>
        {label}
      </label>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full px-3 py-2.5 rounded-lg text-sm outline-none resize-none"
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          color: 'var(--text-primary)',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--accent-cyan)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />
    </div>
  )
}

export function ActionButton({ onClick, loading, children, variant = 'primary', disabled = false }) {
  const styles = {
    primary: { background: 'var(--accent-cyan)', color: '#000', fontWeight: 700 },
    danger: { background: 'var(--accent-red)', color: '#fff', fontWeight: 700 },
    ghost: { background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-muted)' },
  }

  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm transition-all disabled:opacity-50"
      style={styles[variant]}
    >
      {loading && <Loader2 size={14} className="animate-spin" />}
      {children}
    </button>
  )
}

export function RiskBadge({ score, level }) {
  const display = level || (score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : score >= 15 ? 'LOW' : 'CLEAN')
  const cls = `risk-${display.toLowerCase()}`
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold mono border ${cls}`}
    >
      {display} {score !== undefined && `· ${score}/100`}
    </span>
  )
}

export function ResultSection({ title, children }) {
  return (
    <div className="mt-6 animate-fade-in-up">
      <div className="text-xs font-bold mono mb-3 tracking-widest" style={{ color: 'var(--accent-cyan)' }}>
        ── {title}
      </div>
      {children}
    </div>
  )
}

export function LoadingState({ message = 'Running analysis...' }) {
  return (
    <div className="flex items-center gap-3 py-8 justify-center">
      <Loader2 size={20} className="animate-spin" style={{ color: 'var(--accent-cyan)' }} />
      <span className="text-sm mono" style={{ color: 'var(--text-muted)' }}>{message}</span>
    </div>
  )
}

export function ErrorState({ message }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-lg mt-4"
      style={{ background: 'rgba(255,59,59,0.1)', border: '1px solid rgba(255,59,59,0.3)' }}>
      <AlertTriangle size={16} style={{ color: 'var(--accent-red)' }} />
      <span className="text-sm" style={{ color: 'var(--accent-red)' }}>{message}</span>
    </div>
  )
}

export function DataGrid({ data }) {
  if (!data || typeof data !== 'object') return null
  return (
    <div className="space-y-2">
      {Object.entries(data).map(([key, val]) => (
        <div key={key} className="flex items-start justify-between gap-4 py-2 border-b"
          style={{ borderColor: 'var(--border)' }}>
          <span className="text-xs mono" style={{ color: 'var(--text-muted)', minWidth: 160 }}>
            {key.replace(/_/g, ' ').toUpperCase()}
          </span>
          <span className="text-xs text-right" style={{ color: 'var(--text-primary)', wordBreak: 'break-all' }}>
            {Array.isArray(val) ? val.join(', ') || '—'
              : val === null || val === undefined ? '—'
              : typeof val === 'boolean' ? (val ? 'YES' : 'NO')
              : String(val)}
          </span>
        </div>
      ))}
    </div>
  )
}
