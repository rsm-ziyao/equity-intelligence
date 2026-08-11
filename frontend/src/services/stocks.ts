import { ApiError, getJson } from './api'
import type { PricesResponse, StockResponse } from '../types/stock'

export const SUPPORTED_SYMBOLS = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AVGO', 'AMD', 'NFLX'] as const
export const DEFAULT_SYMBOL = 'AAPL'
export type SupportedSymbol = typeof SUPPORTED_SYMBOLS[number]

function requireStockResponse(response: StockResponse) {
  if (!response || typeof response.data?.symbol !== 'string' || !('latest_price' in response.data)) throw new ApiError('The backend returned an invalid stock response.', 200)
  return response
}

function requirePricesResponse(response: PricesResponse) {
  if (!response || !Array.isArray(response.data) || !response.meta || typeof response.meta.symbol !== 'string') throw new ApiError('The backend returned an invalid price history response.', 200)
  return response
}

export function fetchStock(symbol: string, signal?: AbortSignal) { return getJson<StockResponse>(`/stocks/${encodeURIComponent(symbol)}`, signal).then(requireStockResponse) }

export function fetchPrices(symbol: string, params: { startDate?: string; endDate?: string; limit?: number }, signal?: AbortSignal) {
  const query = new URLSearchParams()
  if (params.startDate) query.set('start_date', params.startDate)
  if (params.endDate) query.set('end_date', params.endDate)
  query.set('limit', String(params.limit ?? 100))
  return getJson<PricesResponse>(`/stocks/${encodeURIComponent(symbol)}/prices?${query.toString()}`, signal).then(requirePricesResponse)
}
