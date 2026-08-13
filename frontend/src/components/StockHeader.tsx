import type { Stock } from '../types/stock'
import type { Quote } from '../types/quote'

const freshnessLabels: Record<string, string> = { REALTIME: 'Realtime', DELAYED: 'Delayed', LATEST_TRADING_DAY: 'Latest trading day', STALE: 'Stale', UNAVAILABLE: 'Unavailable' }
const statusLabels: Record<string, string> = { OPEN: 'Market open', CLOSED: 'Market closed', PRE_MARKET: 'Pre-market', POST_MARKET: 'After hours', HOLIDAY: 'Holiday', UNKNOWN: 'Status unavailable' }
function date(value: string) { return new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) }
export default function StockHeader({ stock, symbol, quote, quoteError }: { stock: Stock | null; symbol: string; quote: Quote | null; quoteError?: string | null }) {
  return <div className="selected-identity"><div className="selected-symbol">{stock?.symbol ?? symbol}</div><div className="company-name">{stock?.company_name ?? 'Company details unavailable'}</div>{quote ? <><div className="selected-quote-price">${quote.price.toFixed(2)}</div><div className={`selected-change ${quote.change >= 0 ? 'positive' : 'negative'}`}><span aria-hidden="true">{quote.change >= 0 ? '↑' : '↓'}</span> {quote.change >= 0 ? '+' : ''}{quote.change.toFixed(2)} ({quote.change_percent >= 0 ? '+' : ''}{quote.change_percent.toFixed(2)}%)</div></> : <div className="quote-missing"><strong>Current quote unavailable</strong><span>{quoteError ?? 'Historical daily data is still available below.'}</span></div>}</div>
}
export function QuoteDetails({ quote }: { quote: Quote | null }) {
  if (!quote) return <div className="selected-meta"><span className="freshness freshness-unavailable">Unavailable</span><span>Current quote could not be loaded</span></div>
  return <div className="selected-meta"><span className={`freshness freshness-${quote.freshness.toLowerCase()}`}>{freshnessLabels[quote.freshness]}</span><span>Data provided by {quote.provider === 'finnhub' ? 'Finnhub' : quote.provider}</span><span>Last updated: {date(quote.retrieved_at)}</span><span>{statusLabels[quote.market_status] ?? 'Status unavailable'}</span></div>
}
