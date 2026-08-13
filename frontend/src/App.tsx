import { useEffect, useMemo } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import { DEFAULT_SYMBOL, SUPPORTED_SYMBOLS } from './services/stocks'

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const match = location.pathname.match(/^\/stocks\/([^/]+)\/?$/i)
  const requestedSymbol = match?.[1]?.toUpperCase()
  const routeSymbol = requestedSymbol && SUPPORTED_SYMBOLS.includes(requestedSymbol as typeof SUPPORTED_SYMBOLS[number]) ? requestedSymbol : DEFAULT_SYMBOL
  const symbol = useMemo(() => routeSymbol, [routeSymbol])
  useEffect(() => { if (!match || routeSymbol !== requestedSymbol) navigate(`/stocks/${DEFAULT_SYMBOL}`, { replace: true }) }, [match, navigate, requestedSymbol, routeSymbol])

  return (
    <Dashboard
      symbol={symbol}
      supportedSymbols={SUPPORTED_SYMBOLS}
      onSymbolChange={(nextSymbol) => navigate(`/stocks/${nextSymbol}`)}
    />
  )
}

export default App
