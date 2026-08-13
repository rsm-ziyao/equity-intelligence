import LoadingState from './LoadingState'
import type { QuoteResult } from '../types/quote'

const freshnessLabels: Record<string, string> = { REALTIME: 'Realtime', DELAYED: 'Delayed', LATEST_TRADING_DAY: 'Latest trading day', STALE: 'Stale', UNAVAILABLE: 'Unavailable' }
function money(value: number) { return `$${value.toFixed(2)}` }
function freshness(value: string) { return freshnessLabels[value] ?? 'Unavailable' }

export default function MarketOverview({ results, symbols, loading, error, selected, onSelect }: { results: QuoteResult[]; symbols: readonly string[]; loading: boolean; error: string | null; selected: string; onSelect: (symbol: string) => void }) {
  const bySymbol = new Map(results.map((result) => [result.symbol, result]))
  return <section className="panel overview-panel" aria-labelledby="overview-title">
    <div className="panel-header"><div><h2 id="overview-title" className="panel-title">Market overview</h2><p className="panel-subtitle">Current quotes · updates automatically</p></div><span className="section-kicker">10 supported stocks</span></div>
    {loading && !results.length ? <LoadingState label="Loading current quotes" /> : <>
      <div className="quote-grid">{symbols.map((symbol) => { const { quote, error: quoteError, freshness: resultFreshness } = bySymbol.get(symbol) ?? { quote: null, error: 'No quote returned.', freshness: 'UNAVAILABLE' as const }
        const currentFreshness = quote?.freshness ?? resultFreshness
        const change = quote?.change ?? 0
        const isPositive = change >= 0
        return <button className={`quote-card ${selected === symbol ? 'is-selected' : ''} ${currentFreshness === 'STALE' ? 'is-stale' : ''}`} key={symbol} type="button" aria-pressed={selected === symbol} onClick={() => onSelect(symbol)}>
          <span className="quote-top"><strong>{symbol}</strong><span className={`freshness freshness-${currentFreshness.toLowerCase()}`}>{freshness(currentFreshness)}</span></span>
          {quote ? <><span className="quote-price">{money(quote.price)}</span><span className={`quote-change ${isPositive ? 'positive' : 'negative'}`}><span aria-hidden="true">{isPositive ? '↑' : '↓'}</span> {isPositive ? '+' : ''}{quote.change.toFixed(2)} ({quote.change_percent >= 0 ? '+' : ''}{quote.change_percent.toFixed(2)}%)</span></> : <span className="quote-unavailable"><strong>Current quote unavailable</strong><span>{quoteError ?? 'No current quote returned.'}</span></span>}
        </button>
      })}</div>
      {error && <p className="quote-api-error">Current quotes are unavailable. Historical daily data remains available below.</p>}
    </>}
  </section>
}
