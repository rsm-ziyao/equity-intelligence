import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'

const price = { timestamp: '2026-08-11T14:30:00Z', open: 150, high: 153, low: 149, close: 151, volume: 1000, provider: 'alpha_vantage', provider_timestamp: '2026-08-11T14:30:00Z', retrieved_at: '2026-08-11T15:00:00Z' }
function apiStock(symbol = 'AAPL') { return { data: { symbol, company_name: symbol === 'AAPL' ? 'Apple Inc.' : 'Microsoft Corporation', latest_price: { ...price, close: symbol === 'AAPL' ? 151 : 403 } }, meta: {} } }
function apiPrices(symbol = 'AAPL') { return { data: [{ ...price, close: symbol === 'AAPL' ? 151 : 403 }], meta: { symbol, count: 1, limit: 100, start_date: null, end_date: null } } }
function renderApp() { return render(<BrowserRouter><App /></BrowserRouter>) }

beforeEach(() => { vi.restoreAllMocks() })

describe('stock dashboard', () => {
  it('shows loading state and then renders API-backed stock data', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => { const url = String(input); await new Promise((resolve) => setTimeout(resolve, 5)); return new Response(url.includes('/prices') ? JSON.stringify(apiPrices()) : JSON.stringify(apiStock()), { status: 200, headers: { 'Content-Type': 'application/json' } }) })
    renderApp()
    expect(screen.getAllByText(/Loading/).length).toBeGreaterThan(0)
    expect(await screen.findByText('Apple Inc.')).toBeInTheDocument()
    const summary = screen.getByText('Latest historical close').parentElement
    expect(summary).not.toBeNull()
    expect(within(summary as HTMLElement).getByText('$151.00')).toBeInTheDocument()
    const provider = screen.getByText('Provider').parentElement
    expect(provider).not.toBeNull()
    expect(within(provider as HTMLElement).getByText('Alpha Vantage')).toBeInTheDocument()
    expect(screen.getByText('$153.00')).toBeInTheDocument()
  })

  it('renders a friendly backend error', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify({ error: { code: 'STOCK_NOT_FOUND', message: "Stock symbol 'AAPL' was not found." } }), { status: 404, headers: { 'Content-Type': 'application/json' } }))
    renderApp()
    expect(await screen.findByText('AAPL is not available')).toBeInTheDocument()
    expect(screen.getByText("Stock symbol 'AAPL' was not found.")).toBeInTheDocument()
  })

  it('switches symbols and requests the new route symbol', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => { const url = String(input); const symbol = url.includes('/MSFT') ? 'MSFT' : 'AAPL'; return new Response(url.includes('/prices') ? JSON.stringify(apiPrices(symbol)) : JSON.stringify(apiStock(symbol)), { status: 200, headers: { 'Content-Type': 'application/json' } }) })
    renderApp()
    await screen.findByText('Apple Inc.')
    await userEvent.click(screen.getByRole('button', { name: 'MSFT' }))
    await waitFor(() => expect(screen.getByText('Microsoft Corporation')).toBeInTheDocument())
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/stocks/MSFT'))).toBe(true)
  })
})
