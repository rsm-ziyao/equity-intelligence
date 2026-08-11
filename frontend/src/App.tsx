import { useEffect, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import { DEFAULT_SYMBOL, SUPPORTED_SYMBOLS } from './services/stocks'

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const match = location.pathname.match(/^\/stocks\/([^/]+)\/?$/i)
  const routeSymbol = match?.[1]?.toUpperCase() ?? DEFAULT_SYMBOL
  const symbol = useMemo(() => routeSymbol, [routeSymbol])
  useEffect(() => { if (!match) navigate(`/stocks/${DEFAULT_SYMBOL}`, { replace: true }) }, [match, navigate])

  return (
    <Dashboard
      symbol={symbol}
      supportedSymbols={SUPPORTED_SYMBOLS}
      onSymbolChange={(nextSymbol) => navigate(`/stocks/${nextSymbol}`)}
    />
  )
}

export default App
