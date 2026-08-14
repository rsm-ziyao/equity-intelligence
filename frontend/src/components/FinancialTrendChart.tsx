import type { FinancialTrendPeriod } from '../types/fundamentals'

type Metric = 'revenue' | 'net_income' | 'diluted_eps' | 'free_cash_flow' | 'gross_margin' | 'operating_margin' | 'profit_margin'

const money = (value: number | null) => value == null ? '—' : Math.abs(value) >= 1e9 ? `$${(value / 1e9).toFixed(2)}B` : Math.abs(value) >= 1e6 ? `$${(value / 1e6).toFixed(1)}M` : `$${value.toFixed(2)}`
const valueLabel = (metric: Metric, value: number | null) => metric.includes('margin') ? value == null ? '—' : `${(value * 100).toFixed(1)}%` : metric === 'diluted_eps' ? value == null ? '—' : `$${value.toFixed(2)}` : money(value)
const growthKey = (metric: Metric) => ({ revenue: 'revenue_yoy_growth', net_income: 'net_income_yoy_growth', diluted_eps: 'eps_yoy_growth', free_cash_flow: 'free_cash_flow_yoy_growth' } as const)[metric as 'revenue' | 'net_income' | 'diluted_eps' | 'free_cash_flow']

function periodLabel(period: FinancialTrendPeriod) {
  return period.period_type === 'quarterly' && period.fiscal_quarter != null ? `Q${period.fiscal_quarter} FY${period.fiscal_year}` : `FY${period.fiscal_year}`
}

function pathFor(values: Array<number | null>, min: number, max: number) {
  const segments: string[] = []
  let segment = ''
  values.forEach((value, index) => {
    if (value == null) { if (segment) segments.push(segment); segment = ''; return }
    const x = values.length === 1 ? 50 : 8 + (index / (values.length - 1)) * 84
    const y = max === min ? 50 : 88 - ((value - min) / (max - min)) * 76
    segment += `${segment ? ' L' : 'M'} ${x.toFixed(2)} ${y.toFixed(2)}`
  })
  if (segment) segments.push(segment)
  return segments.join(' ')
}

export default function FinancialTrendChart({ periods, metric, title }: { periods: FinancialTrendPeriod[]; metric: Metric; title: string }) {
  const values = periods.map((period) => period[metric])
  const numeric = values.filter((value): value is number => value != null)
  const min = numeric.length ? Math.min(...numeric) : 0
  const max = numeric.length ? Math.max(...numeric) : 1
  const latest = periods[periods.length - 1]
  const growth = latest && !metric.includes('margin') ? latest[growthKey(metric)] : null
  return <article className="financial-trend-card">
    <div className="trend-card-heading"><h4>{title}</h4><strong>{valueLabel(metric, latest?.[metric] ?? null)}</strong></div>
    <svg className="financial-trend-chart" viewBox="0 0 100 100" role="img" aria-label={`${title} trend`} preserveAspectRatio="none">
      <line x1="8" y1="88" x2="92" y2="88" className="trend-axis" />
      {numeric.length > 0 && <path d={pathFor(values, min, max)} className="trend-line" />}
    </svg>
    <div className="trend-card-footer"><span>{periods.length ? periodLabel(periods[0]) : '—'} → {latest ? periodLabel(latest) : '—'}</span>{growth != null && <span className={growth >= 0 ? 'trend-growth positive' : 'trend-growth negative'}>{growth >= 0 ? '+' : ''}{(growth * 100).toFixed(1)}% YoY</span>}</div>
  </article>
}
