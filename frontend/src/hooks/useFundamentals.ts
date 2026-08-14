import { useEffect, useState } from 'react'
import { fetchFundamentalsHistory } from '../services/fundamentals'
import type { FinancialHistoryResponse } from '../types/fundamentals'

type HistoryState = { response: FinancialHistoryResponse | null; loading: boolean; error: string | null }

const initialState: HistoryState = { response: null, loading: true, error: null }

export function useFundamentals(symbol: string) {
  const [annual, setAnnual] = useState<HistoryState>(initialState)
  const [quarterly, setQuarterly] = useState<HistoryState>(initialState)

  useEffect(() => {
    const controller = new AbortController()
    setAnnual(initialState)
    setQuarterly(initialState)

    const load = (
      periodType: 'annual' | 'quarterly',
      setState: (state: HistoryState) => void,
    ) => {
      fetchFundamentalsHistory(symbol, periodType, 8, controller.signal)
        .then((response) => setState({ response, loading: false, error: null }))
        .catch((reason: unknown) => {
          if (reason instanceof DOMException && reason.name === 'AbortError') return
          setState({ response: null, loading: false, error: reason instanceof Error ? reason.message : 'Unable to load company fundamentals.' })
        })
    }

    load('annual', setAnnual)
    load('quarterly', setQuarterly)
    return () => controller.abort()
  }, [symbol])

  return {
    annual: { data: annual.response?.data ?? null, meta: annual.response?.meta ?? null, loading: annual.loading, error: annual.error },
    quarterly: { data: quarterly.response?.data ?? null, meta: quarterly.response?.meta ?? null, loading: quarterly.loading, error: quarterly.error },
    loading: annual.loading || quarterly.loading,
    error: annual.error || quarterly.error,
  }
}
