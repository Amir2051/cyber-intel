// DarkWebMonitor.jsx
import { useState } from 'react'
import { Eye, Bell, AlertCircle } from 'lucide-react'
import { addMonitorTarget, getAlerts } from '../services/api'
import {
  PageHeader, Card, InputField, SelectField, ActionButton,
  LoadingState, ErrorState
} from '../components/UI'

const KEYWORD_TYPES = [
  { value: 'email', label: 'Email Address' },
  { value: 'name', label: 'Full Name' },
  { value: 'domain', label: 'Domain' },
  { value: 'phone', label: 'Phone Number' },
  { value: 'ssn_prefix', label: 'SSN Prefix' },
]

export function DarkWebMonitor() {
  const [keyword, setKeyword] = useState('')
  const [keywordType, setKeywordType] = useState('email')
  const [clientId] = useState('client-001')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [error, setError] = useState(null)

  const addMonitor = async () => {
    if (!keyword.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const data = await addMonitorTarget(keyword.trim(), keywordType, clientId)
      setResult(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Monitor setup failed')
    } finally {
      setLoading(false)
    }
  }

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const data = await getAlerts(clientId)
      setAlerts(data.data)
    } catch (e) {
      setError('Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader title="DARK WEB MONITOR" subtitle="Keyword surveillance across breach databases and indexed dark sources" icon={Eye} />

      <Card className="mb-4">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="col-span-2">
            <InputField label="MONITOR KEYWORD" value={keyword} onChange={setKeyword} placeholder="keyword to monitor..." />
          </div>
          <SelectField label="TYPE" value={keywordType} onChange={setKeywordType} options={KEYWORD_TYPES} />
        </div>
        <div className="flex gap-3">
          <ActionButton onClick={addMonitor} loading={loading}>Add Monitor</ActionButton>
          <ActionButton onClick={loadAlerts} variant="ghost">View All Alerts</ActionButton>
        </div>
      </Card>

      {loading && <LoadingState message="Scanning sources..." />}
      {error && <ErrorState message={error} />}

      {result && (
        <div className="animate-fade-in-up space-y-4">
          <Card style={{ border: `1px solid ${result.status === 'monitoring_started' ? 'rgba(0,255,136,0.3)' : 'var(--border)'}` }}>
            <div className="text-xs font-bold mono mb-2" style={{ color: 'var(--accent-green)' }}>
              {result.status?.toUpperCase().replace(/_/g, ' ')}
            </div>
            <div className="text-sm" style={{ color: 'var(--text-primary)' }}>Monitoring: <span className="mono">{result.target?.keyword}</span></div>
            {result.initial_scan?.hits > 0 && (
              <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(255,59,59,0.1)', border: '1px solid rgba(255,59,59,0.2)' }}>
                <div className="text-xs font-bold" style={{ color: 'var(--accent-red)' }}>
                  ⚠ INITIAL SCAN: {result.initial_scan.hits} HIT(S) FOUND
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {alerts && (
        <Card className="mt-4">
          <div className="flex items-center gap-2 mb-3">
            <Bell size={14} style={{ color: 'var(--accent-amber)' }} />
            <span className="text-xs font-bold mono" style={{ color: 'var(--accent-amber)' }}>
              ALERTS — {alerts.unread_count} UNREAD
            </span>
          </div>
          {alerts.alerts?.length === 0 ? (
            <div className="text-sm text-center py-4" style={{ color: 'var(--text-muted)' }}>No alerts found</div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {alerts.alerts?.map((a, i) => (
                <div key={i} className="p-3 rounded-lg text-xs"
                  style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                  <div className="flex justify-between mb-1">
                    <span className="mono font-bold" style={{ color: a.severity === 'HIGH' ? 'var(--accent-red)' : 'var(--accent-amber)' }}>
                      {a.severity}
                    </span>
                    <span style={{ color: 'var(--text-muted)' }}>{a.created_at?.split('T')[0]}</span>
                  </div>
                  <div style={{ color: 'var(--text-primary)' }}>
                    {a.finding?.source} — {a.finding?.database_name || a.finding?.type}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

export default DarkWebMonitor
