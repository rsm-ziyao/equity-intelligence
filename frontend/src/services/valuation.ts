import { ApiError, getJson } from './api'
import type { ValuationResponse } from '../types/valuation'

export function fetchValuation(symbol: string, signal?: AbortSignal) {
  return getJson<ValuationResponse>(`/stocks/${encodeURIComponent(symbol)}/valuation`, signal).then((response) => {
    if (!response || !response.meta || !('data' in response) || (response.data !== null && !response.data.metrics)) throw new ApiError('The backend returned an invalid valuation response.', 200)
    return response
  })
}
