import { useEffect, useState } from 'react'
import { fetchValuation } from '../services/valuation'
import type { ValuationResponse } from '../types/valuation'

type State = { response: ValuationResponse | null; loading: boolean; error: string | null }
const initialState: State = { response: null, loading: true, error: null }

export function useValuation(symbol: string) {
  const [state, setState] = useState<State>(initialState)
  useEffect(() => {
    const controller = new AbortController()
    setState(initialState)
    fetchValuation(symbol, controller.signal).then((response) => setState({ response, loading: false, error: null })).catch((reason: unknown) => {
      if (reason instanceof DOMException && reason.name === 'AbortError') return
      setState({ response: null, loading: false, error: reason instanceof Error ? reason.message : 'Unable to load valuation.' })
    })
    return () => controller.abort()
  }, [symbol])
  return { data: state.response?.data ?? null, meta: state.response?.meta ?? null, loading: state.loading, error: state.error }
}
