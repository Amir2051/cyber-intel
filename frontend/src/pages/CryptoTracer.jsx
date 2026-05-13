import { useState } from 'react'
import { Bitcoin, AlertTriangle } from 'lucide-react'
import { cryptoTrace } from '../services/api'
import {
  PageHeader, Card, InputField, SelectField, ActionButton,
  RiskBadge, LoadingState, ErrorState, DataGrid
} from '../components/UI'

const CHAINS = [
  { value: 'eth', label: 'Ethereum (ETH)' },
  { value: 'btc', label: 'Bitcoin (BTC)' },
  { value: 'bnb', label: 'BNB Smart Chain' },
]

export default function CryptoTracer() {
  const [address, setAddress] = useState('')
  const [chain, setChain] = useState('eth')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const run = async () => {
    if (!address.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await cryptoTrace(address.trim(), chain)
      setResult(data.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Trace failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <PageHeader
        title="CRYPTO TRACER"
        subtitle="Wallet transaction graph, risk flagging, and scam address detection"
        icon={Bitcoin}
      />

      <Card>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="col-span-2">
            <InputField label="WALLET ADDRESS" value={address} onChange={setAddress}
              placeholder="0x742d35Cc6634C0532925a3b844Bc..." />
          </div>
          <SelectField label="CHAIN" value={chain} onChange={setChain} options={CHAINS} />
        </div>
        <ActionButton onClick={run} loading={loading}>Trace Wallet</ActionButton>
      </Card>

      {loading && <LoadingState message="Fetching transaction history..." />}
      {error && <ErrorState message={error} />}

      {result && (
        <div className="animate-fade-in-up mt-6 space-y-4">
          {/* Overview */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-xs mono mb-1" style={{ color: 'var(--text-muted)' }}>WALLET</div>
                <div className="font-mono text-sm break-all" style={{ color: 'var(--text-primary)' }}>
                  {result.address}
                </div>
              </div>
              <RiskBadge score={result.risk_score} />
            </div>
            <DataGrid data={result.summary} />
          </Card>

          {/* Risk Flags */}
          {result.risk_flags?.length > 0 && (
            <Card style={{ border: '1px solid rgba(255,59,59,0.3)', background: 'rgba(255,59,59,0.05)' }}>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={14} style={{ color: 'var(--accent-red)' }} />
                <div className="text-xs font-bold mono" style={{ color: 'var(--accent-red)' }}>
                  RISK FLAGS ({result.risk_flags.length})
                </div>
              </div>
              <div className="space-y-1">
                {result.risk_flags.map((flag, i) => (
                  <div key={i} className="text-xs mono py-1.5 px-3 rounded"
                    style={{ background: 'rgba(255,59,59,0.1)', color: 'var(--accent-red)' }}>
                    ⚠ {flag}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Recent Transactions */}
          {result.transactions?.length > 0 && (
            <Card>
              <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>
                RECENT TRANSACTIONS ({result.transactions.length})
              </div>
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {result.transactions.slice(0, 15).map((tx, i) => (
                  <div key={i} className="p-3 rounded-lg text-xs"
                    style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="mono" style={{ color: 'var(--text-muted)' }}>
                        {tx.hash?.slice(0, 20)}...
                      </span>
                      <span className={tx.status === 'success' ? 'text-green-400' : 'text-red-400'}>
                        {tx.status?.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex gap-4" style={{ color: 'var(--text-muted)' }}>
                      <span>FROM: {(tx.from || '').slice(0, 12)}...</span>
                      <span>TO: {(tx.to || '').slice(0, 12)}...</span>
                      <span style={{ color: 'var(--accent-cyan)' }}>
                        {(tx.value_eth || tx.value_btc || tx.value_bnb || 0).toFixed(4)} {chain.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Connected Wallets */}
          {result.connected_wallets?.length > 0 && (
            <Card>
              <div className="text-xs font-bold mono mb-3" style={{ color: 'var(--accent-cyan)' }}>
                CONNECTED WALLETS ({result.connected_wallets.length})
              </div>
              <div className="space-y-1">
                {result.connected_wallets.slice(0, 10).map((w, i) => (
                  <div key={i} className="text-xs mono py-1.5 px-3 rounded"
                    style={{ background: 'var(--bg-secondary)', color: 'var(--text-muted)' }}>
                    {w}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
