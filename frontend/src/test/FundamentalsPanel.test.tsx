import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import FundamentalsPanel from '../components/FundamentalsPanel'

const snapshot = { period_type: 'quarterly', fiscal_year: 2026, fiscal_quarter: 2, period_end: '2026-06-30T00:00:00', filing_date: null, revenue: 100000000, gross_profit: null, operating_income: 20000000, net_income: 10000000, diluted_eps: 1.25, operating_cash_flow: 70000000, capital_expenditures: 20000000, free_cash_flow: 50000000, cash_and_cash_equivalents: null, total_debt: 30000000, gross_margin: null, operating_margin: 0.2, profit_margin: 0.1, currency: 'USD', unit: 'USD', provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00' }
const response = { data: { symbol: 'AAPL', company_name: 'Apple Inc.', financials: { latest_quarterly: snapshot, latest_annual: { ...snapshot, period_type: 'annual', fiscal_quarter: null, fiscal_year: 2025 } }, provenance: { provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00', freshness: 'PERIODIC' } }, meta: { available: true, missing_metrics: ['gross_profit', 'cash_and_cash_equivalents'], periods_returned: 2 } }

describe('FundamentalsPanel', () => {
  beforeEach(() => vi.restoreAllMocks())
  it('renders quarterly and annual snapshots, provenance, and null metrics as dashes', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(response), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<FundamentalsPanel symbol="AAPL" />)
    expect(await screen.findByText('Q2 FY2026')).toBeInTheDocument()
    expect(screen.getByText('FY2025')).toBeInTheDocument()
    expect(screen.getByText('alphavantage')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
    expect(screen.getByText(/Unavailable from provider/)).toBeInTheDocument()
  })
})
