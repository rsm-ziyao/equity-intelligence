import SearchBar from './SearchBar'

export default function StockSelector({ symbols, selected, onChange }: { symbols: readonly string[]; selected: string; onChange: (symbol: string) => void }) {
  return <div className="toolbar"><SearchBar onSearch={onChange} /><nav className="symbol-list" aria-label="Stock symbols">{symbols.map((symbol) => <button className={`symbol-button ${selected === symbol ? 'active' : ''}`} key={symbol} onClick={() => onChange(symbol)} type="button" aria-current={selected === symbol ? 'page' : undefined}>{symbol}</button>)}</nav></div>
}
