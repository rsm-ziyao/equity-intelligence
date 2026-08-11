import type { StockPrice } from '../types/stock'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'

const money = (value: number) => `$${value.toFixed(2)}`
export default function DataTable({ prices, loading, error }: { prices: StockPrice[]; loading: boolean; error: string | null }) {
  if (loading) return <LoadingState label="Loading OHLCV data" />
  if (error) return <ErrorState message={error} />
  if (!prices.length) return <div className="state"><strong>No history found</strong><span>Try widening the date range.</span></div>
  return <div className="table-scroll"><table><thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead><tbody>{[...prices].reverse().map((price) => <tr key={price.timestamp}><td>{new Date(price.timestamp).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' })}</td><td>{money(price.open)}</td><td>{money(price.high)}</td><td>{money(price.low)}</td><td>{money(price.close)}</td><td>{price.volume.toLocaleString()}</td></tr>)}</tbody></table></div>
}
