import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import FinancialAnalysisPanel from '../components/FinancialAnalysisPanel'

const signal = (name: string, status: string, evidence: string[]) => ({ signal: name, status, available: status !== 'UNAVAILABLE', evidence, basis: { period_type: 'annual', latest_period: 'FY2025', comparison_period: 'FY2024', periods_used: 2 }, metrics_used: [], metrics_missing: [] })
const analysis = { data: { symbol: 'AAPL', company_name: 'Apple Inc.', period_type: 'annual', signals: { growth: signal('GROWTH', 'STRONG', ['Revenue YoY +50.1%']), profitability: signal('PROFITABILITY', 'IMPROVING', ['Operating margin +180 bps']), cash_flow: signal('CASH_FLOW', 'WEAKENING', ['FCF changed from $100.0M to $90.0M']), margins: signal('MARGINS', 'EXPANDING', ['Gross margin +120 bps']), financial_strength: signal('FINANCIAL_STRENGTH', 'HEALTHY', ['Cash exceeds total debt']), overall: signal('OVERALL', 'POSITIVE', ['4 positive and 1 negative signals are available']) }, provenance: { provider: 'alphavantage', retrieved_at: '2026-08-14T00:00:00', freshness: 'PERIODIC' } }, meta: { available: true, periods_used: 2, missing_metrics: [], data_availability: {} } }

describe('FinancialAnalysisPanel', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('renders statuses, evidence, overall state, and disclaimer', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(analysis), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<FinancialAnalysisPanel symbol="AAPL" />)
    expect(await screen.findByText('STRONG')).toBeInTheDocument()
    expect(screen.getByText('Revenue YoY +50.1%')).toBeInTheDocument()
    expect(screen.getByText('POSITIVE')).toBeInTheDocument()
    expect(screen.getByText(/not a real-time market signal/)).toBeInTheDocument()
  })

  it('renders unavailable fundamentals without hiding the panel', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ data: null, meta: { available: false, periods_used: 0, missing_metrics: [], data_availability: {}, reason: 'NO_PERSISTED_FUNDAMENTALS' } }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<FinancialAnalysisPanel symbol="NVDA" />)
    expect(await screen.findByText('Financial analysis unavailable')).toBeInTheDocument()
    expect(screen.getByText(/No persisted financial periods/)).toBeInTheDocument()
  })

  it('aborts the previous request when the symbol changes', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Promise<Response>(() => undefined))
    const { rerender } = render(<FinancialAnalysisPanel symbol="AAPL" />)
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    const firstSignal = fetchMock.mock.calls[0][1]?.signal as AbortSignal
    rerender(<FinancialAnalysisPanel symbol="MSFT" />)
    await waitFor(() => expect(firstSignal.aborted).toBe(true))
  })
})
