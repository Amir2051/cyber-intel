import { useState } from 'react'
import { Shield, FolderOpen, Plus, Clock } from 'lucide-react'
import { scoreReputation } from '../services/api'
import {
  PageHeader, Card, InputField, SelectField, ActionButton,
  RiskBadge, LoadingState, ErrorState, DataGrid
} from '../components/UI'

// ── Reputation Scorer ──────────────────────────────────────────

const REP_TYPES = [
  { value: 'email', label: 'Email Address' },
  { value: 'phone', label: 'Phone Number' },
]

export function ReputationScorer() {
  const [value, setValue] = useState('')
  const [valueType, setValueType] = useState('email')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const run = async () => {
    if (!value.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const data = await scoreReputation(value.trim(), valueType)
      setResult(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Scoring failed')
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = (score) => {
    if (score >= 70) return 'var(--accent-red)'
    if (score >= 40) return 'var(--accent-amber)'
    if (score >= 15) return 'var(--accent-cyan)'
    return 'var(--accent-green)'
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader title="REPUTATION SCORER" subtitle="Unified risk scoring for emails and phone numbers (0–100)" icon={Shield} />

      <Card>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="col-span-2">
            <InputField label="VALUE" value={value} onChange={setValue} placeholder="email@domain.com or +1234567890" />
          </div>
          <SelectField label="TYPE" value={valueType} onChange={setValueType} options={REP_TYPES} />
        </div>
        <ActionButton onClick={run} loading={loading}>Score Reputation</ActionButton>
      </Card>

      {loading && <LoadingState message="Querying reputation signals..." />}
      {error && <ErrorState message={error} />}

      {result && (
        <div className="animate-fade-in-up mt-6 space-y-4">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>SUBJECT</div>
                <div className="font-mono font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{result.value}</div>
              </div>
              <div className="text-right">
                <div className="text-5xl font-black mono mb-2" style={{ color: scoreColor(result.risk_score) }}>
                  {result.risk_score}
                </div>
                <RiskBadge level={result.risk_level} />
              </div>
            </div>
            <DataGrid data={result.summary} />
          </Card>

          {result.signals?.map((sig, i) => (
            <Card key={i}>
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-bold mono" style={{ color: 'var(--accent-cyan)' }}>
                  {sig.source?.toUpperCase()}
                </div>
                {sig.score_contribution > 0 && (
                  <span className="text-xs mono" style={{ color: 'var(--accent-red)' }}>
                    +{sig.score_contribution} risk pts
                  </span>
                )}
              </div>
              <DataGrid data={Object.fromEntries(
                Object.entries(sig).filter(([k]) => !['source', 'score_contribution'].includes(k))
              )} />
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default ReputationScorer

// ── Case Manager ───────────────────────────────────────────────

const MOCK_CASES = [
  { id: 'CASE-001', victim: 'John D.', type: 'Crypto Scam', loss: 45000, status: 'Active', date: '2026-05-01' },
  { id: 'CASE-002', victim: 'Sarah M.', type: 'Romance Scam', loss: 12500, status: 'Submitted', date: '2026-04-28' },
  { id: 'CASE-003', victim: 'Robert K.', type: 'Deed Fraud', loss: 280000, status: 'Under Review', date: '2026-04-20' },
]

export function CaseManager() {
  const [cases] = useState(MOCK_CASES)

  const statusColor = (s) => {
    if (s === 'Active') return 'var(--accent-cyan)'
    if (s === 'Submitted') return 'var(--accent-green)'
    return 'var(--accent-amber)'
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader title="CASE MANAGER" subtitle="Track and manage active victim advocacy cases" icon={FolderOpen} />

      <div className="flex justify-between items-center mb-4">
        <div className="text-xs mono" style={{ color: 'var(--text-muted)' }}>{cases.length} ACTIVE CASES</div>
        <ActionButton onClick={() => {}} variant="ghost">
          <Plus size={14} /> New Case
        </ActionButton>
      </div>

      <div className="space-y-3">
        {cases.map(c => (
          <Card key={c.id} className="cursor-pointer transition-all"
            style={{}}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent-cyan)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>{c.id}</div>
                  <div className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{c.victim}</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{c.type}</div>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-xs mono" style={{ color: 'var(--text-muted)' }}>LOSS</div>
                  <div className="font-bold mono" style={{ color: 'var(--accent-red)' }}>
                    ${c.loss.toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>STATUS</div>
                  <span className="text-xs mono font-bold" style={{ color: statusColor(c.status) }}>{c.status}</span>
                </div>
                <div className="flex items-center gap-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                  <Clock size={12} />
                  {c.date}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
