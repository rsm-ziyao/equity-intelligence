import { ApiError, getJson } from './api'
import type { FundamentalsResponse } from '../types/fundamentals'
export function fetchFundamentals(symbol: string, signal?: AbortSignal) { return getJson<FundamentalsResponse>(`/stocks/${encodeURIComponent(symbol)}/fundamentals`, signal).then((response) => { if (!response || !response.meta || !('data' in response)) throw new ApiError('The backend returned an invalid fundamentals response.', 200); return response }) }
