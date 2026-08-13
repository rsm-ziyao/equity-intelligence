import type { StockPrice } from '../types/stock'
export default function PriceSummary({ latest, loading }: { latest: StockPrice | null | undefined; loading: boolean }) {
  if (loading) return <div className="historical-summary"><span>Loading historical data…</span></div>
  return <div className="historical-summary"><span><small>Historical close</small><strong>{latest ? `$${latest.close.toFixed(2)}` : '—'}</strong></span><span><small>Historical data through</small><strong>{latest ? new Date(latest.timestamp).toLocaleDateString([], { dateStyle: 'medium' }) : '—'}</strong></span></div>
}
