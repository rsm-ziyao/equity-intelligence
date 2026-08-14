import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import { useValuation } from '../hooks/useValuation'
import type { ValuationMetric } from '../types/valuation'

function freshnessLabel(value: string) { return value.charAt(0) + value.slice(1).toLowerCase().replace(/_/g, ' ') }
function metricValue(metric: ValuationMetric) { return metric.value == null ? '—' : `${metric.value.toFixed(2)}x` }
function unavailableText(metric: ValuationMetric, label: string) {
  if (metric.status === 'AVAILABLE') return null
  if (metric.reason === 'SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE') return `${label} requires shares outstanding or market capitalization.`
  if (metric.reason === 'NEGATIVE_DENOMINATOR') return 'P/E is unavailable because the annual diluted EPS is negative.'
  if (metric.reason === 'ZERO_DENOMINATOR') return 'P/E is unavailable because the annual diluted EPS is zero.'
  if (metric.reason === 'STALE_MARKET_PRICE') return 'P/E is unavailable because the quote is stale.'
  return 'P/E requires a valid quote and annual diluted EPS.'
}
function MetricRow({ label, metric }: { label: string; metric: ValuationMetric }) { return <div className="valuation-metric"><span>{label}</span><strong>{metricValue(metric)}</strong></div> }

export default function ValuationPanel({ symbol }: { symbol: string }) {
  const { data, loading, error } = useValuation(symbol)
  const body = loading ? <LoadingState label="Loading valuation" /> : error ? <ErrorState message={error} /> : !data ? <div className="state"><strong>Valuation unavailable</strong><span>No quote or annual financial basis is available for {symbol}.</span></div> : <div className="valuation-body">
    <div className="valuation-sections"><div><span className="valuation-label">Market data</span><strong className="valuation-price">{data.market ? `$${data.market.price.toFixed(2)}` : '—'}</strong><small>{data.market ? `${freshnessLabel(data.market.freshness)} · ${data.market.provider}` : 'Quote unavailable'}</small></div><div><span className="valuation-label">Financial basis</span><strong>{data.financial_basis?.label ?? '—'}</strong><small>{data.financial_basis ? `Diluted EPS · through ${new Date(data.financial_basis.period_end).toLocaleDateString()}` : 'Annual diluted EPS unavailable'}</small></div></div>
    <div className="valuation-metrics"><MetricRow label="P/E" metric={data.metrics.pe} /><MetricRow label="P/S" metric={data.metrics.price_to_sales} /><MetricRow label="Price / FCF" metric={data.metrics.price_to_fcf} /></div>
    <div className="valuation-reasons">{([['P/S', data.metrics.price_to_sales], ['Price / FCF', data.metrics.price_to_fcf], ['P/E', data.metrics.pe]] as Array<[string, ValuationMetric]>).map(([label, metric]) => { const text = unavailableText(metric, label); return text ? <p key={`${label}-${metric.reason}`}>{text}</p> : null })}</div>
    <div className="valuation-provenance">Quote status: <strong>{data.market ? freshnessLabel(data.market.freshness) : 'Unavailable'}</strong> · Financial source: <strong>{data.provenance.financial_provider}</strong></div>
  </div>
  return <section className="panel valuation-panel" aria-labelledby="valuation-title"><div className="panel-header"><div><h2 id="valuation-title" className="panel-title">Valuation</h2><p className="panel-subtitle">Descriptive multiples using current market data and reported annual fundamentals</p></div><span className="section-kicker">No verdict</span></div>{body}</section>
}
