export type AnalysisStatus = string

export interface AnalysisBasis {
  period_type: 'annual' | 'quarterly' | null
  latest_period: string | null
  comparison_period: string | null
  periods_used: number
}

export interface AnalysisSignal {
  signal: string
  status: AnalysisStatus
  available: boolean
  evidence: string[]
  basis: AnalysisBasis
  metrics_used: string[]
  metrics_missing: string[]
}

export interface FinancialAnalysisData {
  symbol: string
  company_name: string | null
  period_type: 'annual' | 'quarterly'
  signals: {
    growth: AnalysisSignal
    profitability: AnalysisSignal
    cash_flow: AnalysisSignal
    margins: AnalysisSignal
    financial_strength: AnalysisSignal
    overall: AnalysisSignal
  }
  provenance: { provider: string; retrieved_at: string | null; freshness: string }
}

export interface FinancialAnalysisResponse {
  data: FinancialAnalysisData | null
  meta: {
    available: boolean
    periods_used: number
    missing_metrics: string[]
    data_availability: Record<string, number>
    reason?: string | null
  }
}
