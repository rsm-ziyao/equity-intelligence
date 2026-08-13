import SearchBar from './SearchBar'

export default function StockSelector({ symbols, selected, onChange }: { symbols: readonly string[]; selected: string; onChange: (symbol: string) => void }) {
  return <div className="toolbar"><SearchBar symbols={symbols} selected={selected} onSearch={onChange} /><nav className="symbol-list" aria-label="Supported stock symbols">{symbols.map((symbol) => <button className={`symbol-button ${selected === symbol ? 'active' : ''}`} key={symbol} onClick={() => onChange(symbol)} type="button" aria-pressed={selected === symbol}>{symbol}</button>)}</nav></div>
}
