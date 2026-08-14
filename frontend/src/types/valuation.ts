import type { Freshness, MarketStatus } from './quote'

export interface ValuationMarket { symbol: string; price: number; change: number; change_percent: number; provider: string; provider_timestamp: string; retrieved_at: string; freshness: Freshness; market_status: MarketStatus }
export interface ValuationFinancialBasis { type: 'ANNUAL'; fiscal_year: number; label: string; period_end: string; provider: string; retrieved_at: string; diluted_eps: number }
export type ValuationMetricStatus = 'AVAILABLE' | 'UNAVAILABLE'
export interface ValuationMetric { value: number | null; unit: 'x'; status: ValuationMetricStatus; numerator: string | null; denominator: string | null; reason: string | null }
export interface ValuationData { symbol: string; market: ValuationMarket | null; financial_basis: ValuationFinancialBasis | null; metrics: { pe: ValuationMetric; price_to_sales: ValuationMetric; price_to_fcf: ValuationMetric }; provenance: { quote_provider: string; financial_provider: string } }
export interface ValuationResponse { data: ValuationData | null; meta: { available: boolean; available_metrics: string[]; unavailable_metrics: string[] } }
