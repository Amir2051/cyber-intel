import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import OSINTProfiler from './pages/OSINTProfiler'
import CryptoTracer from './pages/CryptoTracer'
import FraudPackager from './pages/FraudPackager'
import DarkWebMonitor from './pages/DarkWebMonitor'
import DeedFraudScanner from './pages/DeedFraudScanner'
import ReputationScorer from './pages/ReputationScorer'
import CaseManager from './pages/CaseManager'

const PAGES = {
  dashboard: Dashboard,
  osint: OSINTProfiler,
  crypto: CryptoTracer,
  fraud: FraudPackager,
  darkweb: DarkWebMonitor,
  deed: DeedFraudScanner,
  reputation: ReputationScorer,
  cases: CaseManager,
}

export default function App() {
  const [activePage, setActivePage] = useState('dashboard')
  const PageComponent = PAGES[activePage] || Dashboard

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <main className="flex-1 overflow-y-auto">
        <PageComponent />
      </main>
    </div>
  )
}
