import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ValuationPanel from '../components/ValuationPanel'

const market = { symbol: 'AAPL', price: 303.25, change: 1, change_percent: .3, provider: 'finnhub', provider_timestamp: '2026-08-14T12:00:00Z', retrieved_at: '2026-08-14T12:01:00Z', freshness: 'DELAYED', market_status: 'CLOSED' }
const metric = (value: number | null, reason: string | null = null) => ({ value, unit: 'x', status: value == null ? 'UNAVAILABLE' : 'AVAILABLE', numerator: value == null ? null : 'current share price', denominator: value == null ? null : 'FY2025 diluted EPS', reason })
const response = (overrides = {}) => ({ data: { symbol: 'AAPL', market, financial_basis: { type: 'ANNUAL', fiscal_year: 2025, label: 'FY2025', period_end: '2025-06-30T00:00:00Z', provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00Z', diluted_eps: 10.67 }, metrics: { pe: metric(28.42), price_to_sales: metric(null, 'SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE'), price_to_fcf: metric(null, 'SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE') }, provenance: { quote_provider: 'finnhub', financial_provider: 'alphavantage' }, ...overrides }, meta: { available: true, available_metrics: ['pe'], unavailable_metrics: ['price_to_sales', 'price_to_fcf'] } })

beforeEach(() => vi.restoreAllMocks())

describe('ValuationPanel', () => {
  it('renders P/E, annual basis, delayed quote, and deferred metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(response()), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<ValuationPanel symbol="AAPL" />)
    expect(await screen.findByText('28.42x')).toBeInTheDocument()
    expect(screen.getByText('FY2025')).toBeInTheDocument()
    expect(screen.getAllByText(/Delayed/).length).toBeGreaterThan(0)
    expect(screen.getByText('P/S requires shares outstanding or market capitalization.')).toBeInTheDocument()
    expect(screen.getByText('Price / FCF requires shares outstanding or market capitalization.')).toBeInTheDocument()
    expect(screen.queryByText(/BUY|SELL|HOLD|intrinsic value/i)).not.toBeInTheDocument()
  })

  it('renders negative EPS as unavailable without verdict language', async () => {
    const body = response({ metrics: { pe: metric(null, 'NEGATIVE_DENOMINATOR'), price_to_sales: metric(null, 'SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE'), price_to_fcf: metric(null, 'SHARES_OUTSTANDING_OR_MARKET_CAP_UNAVAILABLE') }, financial_basis: { type: 'ANNUAL', fiscal_year: 2025, label: 'FY2025', period_end: '2025-06-30T00:00:00Z', provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00Z', diluted_eps: -1 } })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<ValuationPanel symbol="AAPL" />)
    expect(await screen.findByText('P/E is unavailable because the annual diluted EPS is negative.')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('keeps the panel isolated when valuation fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ error: { message: 'valuation down' } }), { status: 503, headers: { 'Content-Type': 'application/json' } }))
    render(<ValuationPanel symbol="AAPL" />)
    expect(await screen.findByText('valuation down')).toBeInTheDocument()
  })
})
