const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  status: number
  code?: string
  constructor(message: string, status: number, code?: string) { super(message); this.name = 'ApiError'; this.status = status; this.code = code }
}

function isObject(value: unknown): value is Record<string, unknown> { return typeof value === 'object' && value !== null }

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response
  try { response = await fetch(`${API_BASE_URL}${path}`, { signal }) }
  catch (error) { if (error instanceof DOMException && error.name === 'AbortError') throw error; throw new ApiError('The backend is unavailable. Check that the API is running and try again.', 0) }
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const errorBody = body as { error?: { message?: string; code?: string } } | null
    throw new ApiError(errorBody?.error?.message ?? `The request failed (${response.status}).`, response.status, errorBody?.error?.code)
  }
  if (!isObject(body)) throw new ApiError('The backend returned an invalid response.', response.status)
  return body as T
}
