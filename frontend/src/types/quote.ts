export type Freshness = 'REALTIME' | 'DELAYED' | 'LATEST_TRADING_DAY' | 'STALE' | 'UNAVAILABLE'
export type MarketStatus = 'PRE_MARKET' | 'OPEN' | 'POST_MARKET' | 'CLOSED' | 'HOLIDAY' | 'UNKNOWN'

export interface Quote {
  symbol: string
  price: number
  change: number
  change_percent: number
  provider: string
  provider_timestamp: string
  retrieved_at: string
  freshness: Freshness
  market_status: MarketStatus
}

export interface QuoteResult { symbol: string; quote: Quote | null; error: string | null; freshness: Freshness }
export interface QuotesResponse {
  data: QuoteResult[]
  meta: { provider: string; requested_symbol_count: number; returned_symbol_count: number; failed_symbols: string[] }
}
