import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import FinancialTrendChart from './FinancialTrendChart'
import { useFundamentals } from '../hooks/useFundamentals'
import type { FinancialHistoryData, FinancialTrendPeriod } from '../types/fundamentals'

function periodLabel(period: FinancialTrendPeriod) {
  return period.period_type === 'quarterly' && period.fiscal_quarter != null ? `Q${period.fiscal_quarter} FY${period.fiscal_year}` : `FY${period.fiscal_year}`
}

function compactValue(value: number | null, percent = false) {
  if (value == null) return '—'
  if (percent) return `${(value * 100).toFixed(1)}%`
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
  return `$${value.toFixed(2)}`
}

function TrendTable({ data, title }: { data: FinancialHistoryData; title: string }) {
  const rows = data.periods.slice(-4)
  return <div className="trend-table-wrap"><h4>{title}</h4><table className="trend-table"><thead><tr><th>Period</th><th>Revenue</th><th>Net income</th><th>EPS</th><th>FCF</th></tr></thead><tbody>{rows.map((period) => <tr key={`${period.period_end}-${period.fiscal_year}-${period.fiscal_quarter}`}><td>{periodLabel(period)}</td><td>{compactValue(period.revenue)}</td><td>{compactValue(period.net_income)}</td><td>{compactValue(period.diluted_eps)}</td><td>{compactValue(period.free_cash_flow)}</td></tr>)}</tbody></table></div>
}

function TrendSection({ data, meta, title, quarterly = false }: { data: FinancialHistoryData; meta: ReturnType<typeof useFundamentals>['annual']['meta']; title: string; quarterly?: boolean }) {
  return <div className="fundamentals-trend-section"><div className="trend-section-heading"><h3>{title}</h3><span>{data.periods.length} periods</span></div><div className="trend-chart-grid"><FinancialTrendChart periods={data.periods} metric="revenue" title="Revenue" /><FinancialTrendChart periods={data.periods} metric="net_income" title="Net income" /><FinancialTrendChart periods={data.periods} metric="diluted_eps" title="EPS" /><FinancialTrendChart periods={data.periods} metric="free_cash_flow" title="Free cash flow" /></div>{quarterly && <TrendTable data={data} title="Recent quarterly periods" />}<div className="margin-trend"><FinancialTrendChart periods={data.periods} metric="gross_margin" title="Gross margin" /><FinancialTrendChart periods={data.periods} metric="operating_margin" title="Operating margin" /><FinancialTrendChart periods={data.periods} metric="profit_margin" title="Profit margin" /></div>{meta && meta.missing_metrics.length > 0 && <p className="missing-note">Unavailable from provider: {meta.missing_metrics.join(', ')}</p>}</div>
}

export default function FundamentalsPanel({ symbol }: { symbol: string }) {
  const { annual, quarterly } = useFundamentals(symbol)
  const error = annual.error || quarterly.error
  const data = annual.data ?? quarterly.data
  const provider = data?.provenance.provider ?? 'Alpha Vantage'
  const loading = annual.loading || quarterly.loading
  const body = data ? <div className="fundamentals-body"><div className="trend-provenance">Source: {provider} · retrieved {data.provenance.retrieved_at ? new Date(data.provenance.retrieved_at).toLocaleString() : '—'}</div>{annual.data ? <TrendSection data={annual.data} meta={annual.meta} title="Annual trend" /> : annual.loading ? <LoadingState label="Loading annual trend" /> : annual.error ? <ErrorState message={annual.error} /> : null}{quarterly.data ? <TrendSection data={quarterly.data} meta={quarterly.meta} title="Quarterly performance" quarterly /> : quarterly.loading ? <LoadingState label="Loading quarterly performance" /> : quarterly.error ? <ErrorState message={quarterly.error} /> : null}</div> : loading ? <LoadingState label="Loading company fundamentals" /> : error ? <ErrorState message={error} /> : <div className="state"><strong>Fundamentals unavailable</strong><span>No persisted financial periods are available for {symbol}.</span></div>
  return <section className="panel fundamentals-panel" aria-labelledby="fundamentals-title"><div className="panel-header"><div><h2 id="fundamentals-title" className="panel-title">Company fundamentals</h2><p className="panel-subtitle">Persisted Alpha Vantage financial statements · trend history</p></div><span className="section-kicker">{provider}</span></div>{body}</section>
}
