import type { StockPrice } from '../types/stock'

function formatPrice(value: number | undefined) { return value == null ? '—' : `$${value.toFixed(2)}` }
function formatDate(value: string | undefined) { return value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—' }
function formatProvider(value: string | undefined) { return value ? value.split('_').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ') : '—' }
export default function PriceSummary({ latest, loading }: { latest: StockPrice | null | undefined; loading: boolean }) {
  if (loading) return <><div className="summary-cell"><div className="metric-label">Latest historical close</div><div className="metric-value">Loading…</div></div><div className="summary-cell"><div className="metric-label">Provider</div><div className="metric-value">Loading…</div></div><div className="summary-cell"><div className="metric-label">Retrieved</div><div className="metric-value">Loading…</div></div></>
  return <><div className="summary-cell"><div className="metric-label">Latest historical close</div><div className="metric-value price">{formatPrice(latest?.close)}</div></div><div className="summary-cell"><div className="metric-label">Provider</div><div className="metric-value">{formatProvider(latest?.provider)}</div></div><div className="summary-cell"><div className="metric-label">Retrieved</div><div className="metric-value" title={latest?.retrieved_at}>{formatDate(latest?.retrieved_at)}</div></div></>
}
