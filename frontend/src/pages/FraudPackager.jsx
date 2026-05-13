import { useState } from 'react'
import { FileText, Download, ExternalLink, CheckCircle } from 'lucide-react'
import { packageFraudCase } from '../services/api'
import {
  PageHeader, Card, InputField, SelectField, TextArea,
  ActionButton, LoadingState, ErrorState, DataGrid
} from '../components/UI'

const INCIDENT_TYPES = [
  { value: 'crypto_scam', label: 'Cryptocurrency Scam' },
  { value: 'romance_scam', label: 'Romance Scam' },
  { value: 'phishing', label: 'Phishing / Spoofing' },
  { value: 'deed_fraud', label: 'Deed / Real Estate Fraud' },
  { value: 'business_email', label: 'Business Email Compromise' },
  { value: 'identity_theft', label: 'Identity Theft' },
  { value: 'ransomware', label: 'Ransomware' },
]

const AGENCIES = ['IC3', 'FBI', 'SECRET_SERVICE']

export default function FraudPackager() {
  const [form, setForm] = useState({
    victim_name: '', victim_email: '', incident_type: 'crypto_scam',
    incident_date: '', description: '', financial_loss: '',
    suspect_name: '', suspect_email: '', suspect_phone: '',
    target_agencies: ['IC3', 'FBI']
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const set = (key) => (val) => setForm(f => ({ ...f, [key]: val }))

  const toggleAgency = (agency) => {
    setForm(f => ({
      ...f,
      target_agencies: f.target_agencies.includes(agency)
        ? f.target_agencies.filter(a => a !== agency)
        : [...f.target_agencies, agency]
    }))
  }

  const run = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const payload = {
        case_id: `CASE-${Date.now()}`,
        victim_name: form.victim_name,
        victim_email: form.victim_email,
        incident_type: form.incident_type,
        incident_date: form.incident_date,
        description: form.description,
        financial_loss: parseFloat(form.financial_loss) || 0,
        suspect_info: {
          name: form.suspect_name,
          email: form.suspect_email,
          phone: form.suspect_phone,
        },
        target_agencies: form.target_agencies
      }
      const data = await packageFraudCase(payload)
      setResult(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Packaging failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader
        title="CASE PACKAGER"
        subtitle="Format victim cases into IC3, FBI, and Secret Service ready report bundles"
        icon={FileText}
      />

      <div className="space-y-4">
        {/* Victim Info */}
        <Card>
          <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── VICTIM INFORMATION</div>
          <div className="grid grid-cols-2 gap-4">
            <InputField label="VICTIM NAME" value={form.victim_name} onChange={set('victim_name')} placeholder="Full legal name" />
            <InputField label="VICTIM EMAIL" value={form.victim_email} onChange={set('victim_email')} placeholder="email@domain.com" />
          </div>
        </Card>

        {/* Incident */}
        <Card>
          <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── INCIDENT DETAILS</div>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <SelectField label="INCIDENT TYPE" value={form.incident_type} onChange={set('incident_type')} options={INCIDENT_TYPES} />
            <InputField label="INCIDENT DATE" value={form.incident_date} onChange={set('incident_date')} type="date" />
            <InputField label="FINANCIAL LOSS (USD)" value={form.financial_loss} onChange={set('financial_loss')} placeholder="0.00" type="number" />
          </div>
          <TextArea label="INCIDENT DESCRIPTION" value={form.description} onChange={set('description')}
            placeholder="Detailed description of what occurred..." />
        </Card>

        {/* Suspect */}
        <Card>
          <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── SUSPECT INFORMATION (if known)</div>
          <div className="grid grid-cols-3 gap-4">
            <InputField label="SUSPECT NAME" value={form.suspect_name} onChange={set('suspect_name')} placeholder="Known alias or name" />
            <InputField label="SUSPECT EMAIL" value={form.suspect_email} onChange={set('suspect_email')} placeholder="Known email" />
            <InputField label="SUSPECT PHONE" value={form.suspect_phone} onChange={set('suspect_phone')} placeholder="+1..." />
          </div>
        </Card>

        {/* Agencies */}
        <Card>
          <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── TARGET AGENCIES</div>
          <div className="flex gap-3">
            {AGENCIES.map(a => (
              <button key={a}
                onClick={() => toggleAgency(a)}
                className="px-4 py-2 rounded-lg text-sm mono font-bold transition-all"
                style={{
                  background: form.target_agencies.includes(a) ? 'rgba(0,212,255,0.15)' : 'var(--bg-secondary)',
                  border: `1px solid ${form.target_agencies.includes(a) ? 'var(--accent-cyan)' : 'var(--border)'}`,
                  color: form.target_agencies.includes(a) ? 'var(--accent-cyan)' : 'var(--text-muted)'
                }}>
                {a}
              </button>
            ))}
          </div>
        </Card>

        <ActionButton onClick={run} loading={loading}>Generate Report Bundle</ActionButton>
      </div>

      {loading && <LoadingState message="Packaging case for agency submission..." />}
      {error && <ErrorState message={error} />}

      {result && (
        <div className="animate-fade-in-up mt-6 space-y-4">
          <Card style={{ border: '1px solid rgba(0,255,136,0.3)' }}>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle size={16} style={{ color: 'var(--accent-green)' }} />
              <span className="font-bold mono" style={{ color: 'var(--accent-green)' }}>REPORT BUNDLE GENERATED</span>
            </div>
            <DataGrid data={result.summary} />
          </Card>

          {/* Submission Links */}
          <Card>
            <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── SUBMISSION LINKS</div>
            <div className="space-y-2">
              {Object.entries(result.submission_links || {}).map(([agency, url]) => (
                <a key={agency} href={url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:opacity-80 transition-opacity"
                  style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--accent-cyan)' }}>
                  <ExternalLink size={14} />
                  <span className="font-bold mono">{agency}</span>
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{url}</span>
                </a>
              ))}
            </div>
          </Card>

          {/* Next Steps */}
          <Card>
            <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>── NEXT STEPS</div>
            <div className="space-y-2">
              {result.next_steps?.map((step, i) => (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <span className="mono text-xs mt-0.5" style={{ color: 'var(--accent-cyan)' }}>{i + 1}.</span>
                  <span style={{ color: 'var(--text-primary)' }}>{step}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
