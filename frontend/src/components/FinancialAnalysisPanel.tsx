import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import { useFinancialAnalysis } from '../hooks/useFinancialAnalysis'
import type { AnalysisSignal, FinancialAnalysisData } from '../types/financialAnalysis'

const labels: Array<[keyof FinancialAnalysisData['signals'], string]> = [
  ['growth', 'Growth'],
  ['profitability', 'Profitability'],
  ['cash_flow', 'Cash flow'],
  ['margins', 'Margins'],
  ['financial_strength', 'Financial strength'],
]

function SignalCard({ label, signal }: { label: string; signal: AnalysisSignal }) {
  return <article className={`analysis-signal analysis-${signal.status.toLowerCase()}`}>
    <div className="analysis-signal-heading"><span>{label}</span><strong>{signal.available ? signal.status : 'UNAVAILABLE'}</strong></div>
    {signal.evidence.length > 0 ? <ul>{signal.evidence.slice(0, 2).map((item) => <li key={item}>{item}</li>)}</ul> : <p>No supporting persisted data is available.</p>}
  </article>
}

export default function FinancialAnalysisPanel({ symbol }: { symbol: string }) {
  const { data, meta, loading, error } = useFinancialAnalysis(symbol)
  const body = loading ? <LoadingState label="Loading financial analysis" /> : error ? <ErrorState message={error} /> : !data ? <div className="state"><strong>Financial analysis unavailable</strong><span>No persisted financial periods are available for {symbol}.</span></div> : <>
    <div className="analysis-grid">{labels.map(([key, label]) => <SignalCard key={key} label={label} signal={data.signals[key]} />)}</div>
    {data.signals.overall.available && <div className="analysis-overall"><span>Overall</span><strong>{data.signals.overall.status}</strong><small>{data.signals.overall.evidence[0]}</small></div>}
  </>
  return <section className="panel financial-analysis-panel" aria-labelledby="financial-analysis-title"><div className="panel-header"><div><h2 id="financial-analysis-title" className="panel-title">Financial analysis</h2><p className="panel-subtitle">Based on persisted periodic financial statements · not a real-time market signal</p></div><span className="section-kicker">{meta?.available ? data?.period_type : 'Unavailable'}</span></div><div className="financial-analysis-body">{body}</div></section>
}
