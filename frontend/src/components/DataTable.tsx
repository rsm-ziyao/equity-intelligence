import type { StockPrice } from '../types/stock'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
const money = (value: number) => `$${value.toFixed(2)}`
function volume(value: number) { return value >= 1000000 ? `${(value / 1000000).toFixed(1).replace('.0', '')}M` : value >= 1000 ? `${(value / 1000).toFixed(1).replace('.0', '')}K` : String(value) }
export default function DataTable({ prices, loading, error }: { prices: StockPrice[]; loading: boolean; error: string | null }) {
  if (loading) return <LoadingState label="Loading historical daily data" />
  if (error) return <ErrorState message={error} />
  if (!prices.length) return <div className="state"><strong>No historical daily data found</strong><span>Try a wider range.</span></div>
  return <div className="table-scroll"><table><caption className="sr-only">Historical daily OHLCV records</caption><thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead><tbody>{[...prices].reverse().map((price) => <tr key={price.timestamp}><td>{new Date(price.timestamp).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' })}</td><td>{money(price.open)}</td><td>{money(price.high)}</td><td>{money(price.low)}</td><td>{money(price.close)}</td><td title={price.volume.toLocaleString()}>{volume(price.volume)}</td></tr>)}</tbody></table></div>
}
