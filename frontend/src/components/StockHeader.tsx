import type { Stock } from '../types/stock'

export default function StockHeader({ stock, symbol }: { stock: Stock | null; symbol: string }) {
  return <div className="summary-cell"><div className="summary-symbol">{stock?.symbol ?? symbol}</div><div className="company-name">{stock?.company_name ?? 'Company details will appear when available.'}</div></div>
}
