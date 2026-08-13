import { useEffect, useState } from 'react'
import { fetchPrices, fetchStock } from '../services/stocks'
import type { Stock, StockPrice } from '../types/stock'

export function useStock(symbol: string, startDate: string, endDate: string) {
  const [stock, setStock] = useState<Stock | null>(null)
  const [prices, setPrices] = useState<StockPrice[]>([])
  const [loading, setLoading] = useState(true)
  const [pricesLoading, setPricesLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pricesError, setPricesError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setPricesLoading(true); setError(null); setPricesError(null); setStock(null); setPrices([])
    fetchStock(symbol, controller.signal)
      .then((response) => setStock(response.data))
      .catch((reason: unknown) => { if (reason instanceof DOMException && reason.name === 'AbortError') return; setError(reason instanceof Error ? reason.message : 'Unable to load this stock.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    fetchPrices(symbol, { startDate, endDate }, controller.signal)
      .then((response) => setPrices(response.data))
      .catch((reason: unknown) => { if (reason instanceof DOMException && reason.name === 'AbortError') return; setPricesError(reason instanceof Error ? reason.message : 'Unable to load historical data.') })
      .finally(() => { if (!controller.signal.aborted) setPricesLoading(false) })
    return () => controller.abort()
  }, [symbol, startDate, endDate])

  return { stock, prices, loading, pricesLoading, error, pricesError }
}
