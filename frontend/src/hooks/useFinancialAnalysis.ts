import { useEffect, useState } from 'react'
import { fetchFinancialAnalysis } from '../services/financialAnalysis'
import type { FinancialAnalysisData, FinancialAnalysisResponse } from '../types/financialAnalysis'

type State = { response: FinancialAnalysisResponse | null; loading: boolean; error: string | null }
const initialState: State = { response: null, loading: true, error: null }

export function useFinancialAnalysis(symbol: string) {
  const [state, setState] = useState<State>(initialState)

  useEffect(() => {
    const controller = new AbortController()
    setState(initialState)
    fetchFinancialAnalysis(symbol, 'annual', 8, controller.signal)
      .then((response) => setState({ response, loading: false, error: null }))
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === 'AbortError') return
        setState({ response: null, loading: false, error: reason instanceof Error ? reason.message : 'Unable to load financial analysis.' })
      })
    return () => controller.abort()
  }, [symbol])

  return {
    data: state.response?.data as FinancialAnalysisData | null,
    meta: state.response?.meta ?? null,
    loading: state.loading,
    error: state.error,
  }
}
