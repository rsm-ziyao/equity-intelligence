import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import FundamentalsPanel from '../components/FundamentalsPanel'

const period = (period_type: 'annual' | 'quarterly', fiscal_year: number, fiscal_quarter: number | null, revenue: number | null = 100000000) => ({ period_type, fiscal_year, fiscal_quarter, period_start: null, period_end: `${fiscal_year}-06-30T00:00:00`, filing_date: null, revenue, gross_profit: 40000000, operating_income: 20000000, net_income: 10000000, diluted_eps: 1.25, operating_cash_flow: 70000000, capital_expenditures: 20000000, free_cash_flow: 50000000, cash_and_cash_equivalents: null, total_debt: 30000000, gross_margin: 0.4, operating_margin: 0.2, profit_margin: 0.1, revenue_yoy_growth: 0.25, net_income_yoy_growth: 0.1, eps_yoy_growth: 0.05, free_cash_flow_yoy_growth: 0.2, currency: 'USD', unit: 'USD', provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00' })
const history = (period_type: 'annual' | 'quarterly') => ({ data: { symbol: 'AAPL', company_name: 'Apple Inc.', period_type, periods: period_type === 'annual' ? [period('annual', 2024, null), period('annual', 2025, null, 125000000)] : [period('quarterly', 2025, 2), period('quarterly', 2026, 2, 125000000)], provenance: { provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00', freshness: 'PERIODIC' } }, meta: { available: true, missing_metrics: ['cash_and_cash_equivalents'], periods_returned: 2, requested_limit: 8, metric_coverage: { revenue: 2 }, missing_periods: [] } })

describe('FundamentalsPanel', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('renders annual, quarterly, margin trends, YoY, and provenance', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => new Response(JSON.stringify(String(input).includes('period_type=quarterly') ? history('quarterly') : history('annual')), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<FundamentalsPanel symbol="AAPL" />)
    expect(await screen.findByText('Annual trend')).toBeInTheDocument()
    expect(screen.getByText('Quarterly performance')).toBeInTheDocument()
    expect(screen.getAllByText('Revenue').length).toBeGreaterThan(0)
    expect(screen.getAllByText('+25.0% YoY').length).toBeGreaterThan(0)
    expect(screen.getByText('alphavantage')).toBeInTheDocument()
    expect(screen.getAllByText(/Unavailable from provider/).length).toBeGreaterThan(0)
  })

  it('shows unavailable fundamentals without hiding the panel shell', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify({ data: null, meta: { available: false, periods_returned: 0, requested_limit: 8, missing_metrics: [], metric_coverage: {}, missing_periods: [] } }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<FundamentalsPanel symbol="NVDA" />)
    expect(await screen.findByText('Fundamentals unavailable')).toBeInTheDocument()
    expect(screen.getByText(/No persisted financial periods/)).toBeInTheDocument()
  })

  it('clears stale trend data when the symbol changes', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const symbol = String(input).includes('MSFT') ? 'MSFT' : 'AAPL'
      const body = history('annual')
      return new Response(JSON.stringify(symbol === 'AAPL' ? body : { ...body, data: { ...body.data, symbol, company_name: 'Microsoft Corporation' } }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    })
    const { rerender } = render(<FundamentalsPanel symbol="AAPL" />)
    expect(await screen.findByText('Annual trend')).toBeInTheDocument()
    rerender(<FundamentalsPanel symbol="MSFT" />)
    await waitFor(() => expect(screen.getByText('Annual trend')).toBeInTheDocument())
  })
})
