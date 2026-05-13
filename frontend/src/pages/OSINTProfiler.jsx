import { useState } from 'react'
import { Search } from 'lucide-react'
import { osintProfile } from '../services/api'
import {
  PageHeader, Card, InputField, SelectField, ActionButton,
  RiskBadge, ResultSection, LoadingState, ErrorState, DataGrid
} from '../components/UI'

const TYPES = [
  { value: 'email', label: 'Email Address' },
  { value: 'username', label: 'Username' },
  { value: 'phone', label: 'Phone Number' },
  { value: 'domain', label: 'Domain / Website' },
]

export default function OSINTProfiler() {
  const [query, setQuery] = useState('')
  const [queryType, setQueryType] = useState('email')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const run = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await osintProfile(query.trim(), queryType)
      setResult(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader
        title="OSINT PROFILER"
        subtitle="Automated actor dossier generation from email, username, phone, or domain"
        icon={Search}
      />

      <Card>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="col-span-2">
            <InputField label="QUERY" value={query} onChange={setQuery} placeholder="email@domain.com / @username / +1234567890" />
          </div>
          <SelectField label="TYPE" value={queryType} onChange={setQueryType} options={TYPES} />
        </div>
        <ActionButton onClick={run} loading={loading}>
          Run OSINT Profile
        </ActionButton>
      </Card>

      {loading && <LoadingState message="Aggregating intelligence sources..." />}
      {error && <ErrorState message={error} />}

      {result && (
        <div className="animate-fade-in-up mt-6 space-y-4">
          {/* Risk score header */}
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>SUBJECT</div>
                <div className="font-bold mono text-lg" style={{ color: 'var(--text-primary)' }}>{result.query}</div>
                <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{result.timestamp}</div>
              </div>
              <div className="text-right">
                <div className="text-xs mono mb-2" style={{ color: 'var(--text-muted)' }}>RISK SCORE</div>
                <RiskBadge score={result.risk_score} />
              </div>
            </div>
          </Card>

          {/* Source findings */}
          {result.sources?.map((source, i) => (
            <Card key={i}>
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-bold mono" style={{ color: 'var(--accent-cyan)' }}>
                  {source.source?.toUpperCase() || `SOURCE ${i + 1}`}
                </div>
                <span className={`text-xs mono px-2 py-0.5 rounded ${
                  source.status === 'success' || source.status === 'found'
                    ? 'text-green-400 bg-green-400/10'
                    : 'text-yellow-400 bg-yellow-400/10'
                }`}>
                  {source.status?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
              <DataGrid data={source.data} />
            </Card>
          ))}

          {/* Aggregated findings */}
          {result.findings && Object.keys(result.findings).length > 0 && (
            <Card>
              <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>
                AGGREGATED FINDINGS
              </div>
              <DataGrid data={result.findings} />
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
