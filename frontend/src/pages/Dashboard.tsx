import { useMemo, useState } from 'react'
import DataTable from '../components/DataTable'
import PriceChart from '../components/PriceChart'
import PriceSummary from '../components/PriceSummary'
import StockHeader, { QuoteDetails } from '../components/StockHeader'
import StockSelector from '../components/StockSelector'
import { useStock } from '../hooks/useStock'
import { useQuotes } from '../hooks/useQuotes'
import MarketOverview from '../components/MarketOverview'
import FundamentalsPanel from '../components/FundamentalsPanel'
import FinancialAnalysisPanel from '../components/FinancialAnalysisPanel'
import ValuationPanel from '../components/ValuationPanel'

function dateString(date: Date) { return date.toISOString().slice(0, 10) }
const ranges = [{ label: '5D', days: 7 }, { label: '1M', days: 31 }, { label: '3M', days: 93 }, { label: '6M', days: 186 }, { label: '1Y', days: 366 }, { label: 'MAX', days: null }]
export default function Dashboard({ symbol, supportedSymbols, onSymbolChange }: { symbol: string; supportedSymbols: readonly string[]; onSymbolChange: (symbol: string) => void }) {
  const today = new Date(), [range, setRange] = useState('1Y'), [endDate, setEndDate] = useState(dateString(today)), [startDate, setStartDate] = useState(dateString(new Date(today.getFullYear() - 1, today.getMonth(), today.getDate())))
  const { stock, prices, loading, pricesLoading, error, pricesError } = useStock(symbol, startDate, endDate)
  const { quotes, loading: quotesLoading, error: quotesError } = useQuotes(supportedSymbols)
  const selectedQuote = useMemo(() => quotes.find((result) => result.symbol === symbol), [quotes, symbol])
  function selectRange(label: string, days: number | null) { setRange(label); setEndDate(dateString(today)); setStartDate(days == null ? '2000-01-01' : dateString(new Date(today.getTime() - days * 86400000))) }
  return <div className="app-shell"><header className="topbar"><div className="brand"><span className="brand-mark">EI</span><span className="brand-name">Equity Intelligence</span></div><div className="topbar-note">CURRENT QUOTES · DAILY HISTORY</div></header><main className="page">
    <div className="page-heading"><div><div className="eyebrow">United States / Equities</div><h1>Market view</h1><p className="heading-copy">Research current market signals alongside independent historical daily data.</p></div><div className="data-note">Current quotes update automatically.<br />Historical data is sourced from persisted daily records.</div></div>
    <MarketOverview results={quotes} symbols={supportedSymbols} loading={quotesLoading} error={quotesError} selected={symbol} onSelect={onSymbolChange} />
    <StockSelector symbols={supportedSymbols} selected={symbol} onChange={onSymbolChange} />
    <section className="panel selected-panel" aria-labelledby="selected-stock-title"><div className="selected-heading"><div><div className="eyebrow">Selected stock</div><h2 id="selected-stock-title">{symbol} research</h2></div><QuoteDetails quote={selectedQuote?.quote ?? null} /></div><div className="selected-grid"><StockHeader stock={stock} symbol={symbol} quote={selectedQuote?.quote ?? null} quoteError={selectedQuote?.error} /><PriceSummary latest={stock?.latest_price} loading={loading} /></div></section>
    <FundamentalsPanel symbol={symbol} />
    <FinancialAnalysisPanel symbol={symbol} />
    <ValuationPanel symbol={symbol} />
    <section className="panel chart-panel"><div className="panel-header"><div><h2 className="panel-title">Historical daily closing price</h2><p className="panel-subtitle">{symbol} · {range} · {prices.length} trading-day observations</p></div><div className="range-controls" role="group" aria-label="Historical price range">{ranges.map(({ label, days }) => <button key={label} type="button" className={range === label ? 'range-button active' : 'range-button'} onClick={() => selectRange(label, days)}>{label}</button>)}</div></div><PriceChart prices={prices} loading={pricesLoading} error={pricesError} symbol={symbol} range={range} /></section>
    <details className="panel data-section" open><summary><span><strong>Historical daily data</strong><small>Historical daily records — not current quote data.</small></span><span className="details-toggle">Show / hide</span></summary><DataTable prices={prices} loading={pricesLoading} error={pricesError} /></details>
    <details className="panel provenance-section"><summary><span><strong>Data details</strong><small>Source and freshness information</small></span><span className="details-toggle">Show details</span></summary><div className="provenance"><div>Current quotes: <strong>{selectedQuote?.quote?.provider === 'finnhub' ? 'Finnhub' : selectedQuote?.quote?.provider ?? 'Unavailable'}</strong></div><div>Historical daily data: <strong>{stock?.latest_price?.provider === 'alpha_vantage' ? 'Alpha Vantage via PostgreSQL' : stock?.latest_price?.provider ?? 'Unavailable'}</strong></div><div>Historical data through: <strong>{stock?.latest_price?.provider_timestamp ? new Date(stock.latest_price.provider_timestamp).toLocaleString() : '—'}</strong></div></div></details>
    {error && !stock && <div className="state error panel"><strong>{symbol} details unavailable</strong><span>{error}</span><span>Historical daily data may still be available below.</span></div>}
  </main></div>
}
