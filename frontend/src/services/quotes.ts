import { ApiError, getJson } from './api'
import type { QuotesResponse } from '../types/quote'

function requireQuotesResponse(response: QuotesResponse) {
  if (!response || !Array.isArray(response.data) || !response.meta || !Array.isArray(response.meta.failed_symbols)) throw new ApiError('The backend returned an invalid quote response.', 200)
  return response
}

export function fetchQuotes(symbols: readonly string[], signal?: AbortSignal) {
  const query = new URLSearchParams({ symbols: symbols.join(',') })
  return getJson<QuotesResponse>(`/quotes?${query.toString()}`, signal).then(requireQuotesResponse)
}
