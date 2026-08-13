import { useEffect, useState } from 'react'
import { fetchQuotes } from '../services/quotes'
import type { QuoteResult } from '../types/quote'

export function useQuotes(symbols: readonly string[], intervalMs = 45000) {
  const [quotes, setQuotes] = useState<QuoteResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    let timer: number | undefined
    const load = async () => {
      if (document.visibilityState !== 'visible' && quotes.length) return
      const controller = new AbortController()
      try {
        if (!quotes.length) setLoading(true)
        const response = await fetchQuotes(symbols, controller.signal)
        if (active) { setQuotes(response.data); setError(null) }
      } catch (reason) {
        if (reason instanceof DOMException && reason.name === 'AbortError') return
        if (active) setError(reason instanceof Error ? reason.message : 'Unable to load current quotes.')
      } finally {
        if (active) setLoading(false)
      }
    }
    const schedule = () => { window.clearTimeout(timer); timer = window.setTimeout(() => { void load(); schedule() }, intervalMs) }
    const onVisibility = () => { if (document.visibilityState === 'visible') void load() }
    void load(); schedule(); document.addEventListener('visibilitychange', onVisibility)
    return () => { active = false; window.clearTimeout(timer); document.removeEventListener('visibilitychange', onVisibility) }
  }, [symbols, intervalMs])

  return { quotes, loading, error }
}
