import type { StockPrice } from '../types/stock'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'

export default function PriceChart({ prices, loading, error }: { prices: StockPrice[]; loading: boolean; error: string | null }) {
  if (loading) return <LoadingState label="Loading price history" />
  if (error) return <ErrorState message={error} />
  if (!prices.length) return <div className="chart-empty">No persisted prices match this date range.</div>
  const width = 700, height = 290, pad = { top: 15, right: 8, bottom: 30, left: 48 }
  const values = prices.map((price) => price.close), min = Math.min(...values), max = Math.max(...values), spread = max - min || 1
  const x = (index: number) => pad.left + (index / Math.max(prices.length - 1, 1)) * (width - pad.left - pad.right)
  const y = (value: number) => pad.top + ((max - value) / spread) * (height - pad.top - pad.bottom)
  const points = prices.map((price, index) => `${x(index)},${y(price.close)}`).join(' ')
  const area = `${pad.left},${height - pad.bottom} ${points} ${x(prices.length - 1)},${height - pad.bottom}`
  const ticks = [0, .5, 1].map((ratio) => max - spread * ratio)
  const labelIndexes = Array.from(new Set([0, Math.floor((prices.length - 1) / 2), prices.length - 1]))
  return <div className="chart-wrap"><svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Historical closing price chart"><defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#d8a676" stopOpacity=".22" /><stop offset="1" stopColor="#d8a676" stopOpacity="0" /></linearGradient></defs>{ticks.map((value) => <g key={value}><line className="chart-grid-line" x1={pad.left} x2={width - pad.right} y1={y(value)} y2={y(value)} /><text className="chart-label" x="0" y={y(value) + 4}>${value.toFixed(2)}</text></g>)}<polygon className="chart-area" points={area} /><polyline className="chart-line" points={points} />{labelIndexes.map((index) => <text className="chart-label" key={index} textAnchor={index === 0 ? 'start' : index === prices.length - 1 ? 'end' : 'middle'} x={x(index)} y={height - 8}>{new Date(prices[index].timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}</text>)}</svg></div>
}
