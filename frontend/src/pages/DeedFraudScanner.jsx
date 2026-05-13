import { useState } from 'react'
import { Home, AlertTriangle, CheckCircle } from 'lucide-react'
import { scanDeedFraud } from '../services/api'
import {
  PageHeader, Card, InputField, ActionButton,
  RiskBadge, LoadingState, ErrorState, DataGrid
} from '../components/UI'

export default function DeedFraudScanner() {
  const [form, setForm] = useState({ address: '', owner: '', county: '', state: '' })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const set = k => v => setForm(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const data = await scanDeedFraud(form.address, form.owner, form.county, form.state)
      setResult(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader title="DEED FRAUD SCANNER" subtitle="Property transfer anomaly detection and ownership verification" icon={Home} />

      <Card>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <InputField label="PROPERTY ADDRESS" value={form.address} onChange={set('address')} placeholder="123 Main St" />
          <InputField label="OWNER NAME" value={form.owner} onChange={set('owner')} placeholder="Full legal name on deed" />
          <InputField label="COUNTY" value={form.county} onChange={set('county')} placeholder="Los Angeles" />
          <InputField label="STATE" value={form.state} onChange={set('state')} placeholder="CA" />
        </div>
        <ActionButton onClick={run} loading={loading}>Scan for Deed Fraud</ActionButton>
      </Card>

      {loading && <LoadingState message="Querying property records..." />}
      {error && <ErrorState message={error} />}

      {result && (
        <div className="animate-fade-in-up mt-6 space-y-4">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>PROPERTY</div>
                <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>{result.property_address}</div>
              </div>
              <RiskBadge score={result.risk_score} />
            </div>
            <DataGrid data={result.property_data} />
          </Card>

          {result.risk_flags?.length > 0 && (
            <Card style={{ border: '1px solid rgba(255,59,59,0.3)' }}>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={14} style={{ color: 'var(--accent-red)' }} />
                <span className="text-xs font-bold mono" style={{ color: 'var(--accent-red)' }}>FRAUD INDICATORS</span>
              </div>
              {result.risk_flags.map((f, i) => (
                <div key={i} className="text-xs mono py-1.5 px-3 rounded mb-1"
                  style={{ background: 'rgba(255,59,59,0.1)', color: 'var(--accent-red)' }}>
                  ⚠ {f.replace(/_/g, ' ')}
                </div>
              ))}
            </Card>
          )}

          <Card>
            <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── RECOMMENDATIONS</div>
            {result.recommendations?.map((r, i) => (
              <div key={i} className="flex items-start gap-3 text-sm mb-2">
                <CheckCircle size={14} className="mt-0.5 flex-shrink-0" style={{ color: 'var(--accent-green)' }} />
                <span style={{ color: 'var(--text-primary)' }}>{r}</span>
              </div>
            ))}
          </Card>
        </div>
      )}
    </div>
  )
}
