export interface StockPrice {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  provider: string
  provider_timestamp: string
  retrieved_at: string
}

export interface Stock {
  symbol: string
  company_name: string | null
  latest_price: StockPrice | null
}

export interface StockResponse { data: Stock; meta: Record<string, unknown> }
export interface PricesMeta { symbol: string; count: number; limit: number; start_date: string | null; end_date: string | null }
export interface PricesResponse { data: StockPrice[]; meta: PricesMeta }
