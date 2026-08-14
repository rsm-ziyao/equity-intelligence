import { ApiError, getJson } from './api'
import type { FinancialAnalysisResponse } from '../types/financialAnalysis'

export function fetchFinancialAnalysis(symbol: string, periodType: 'annual' | 'quarterly' = 'annual', limit = 8, signal?: AbortSignal) {
  return getJson<FinancialAnalysisResponse>(`/stocks/${encodeURIComponent(symbol)}/fundamentals/analysis?period_type=${periodType}&limit=${limit}`, signal).then((response) => {
    if (!response || !response.meta || !('data' in response) || (response.data !== null && !response.data.signals)) throw new ApiError('The backend returned an invalid financial analysis response.', 200)
    return response
  })
}
