import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'

export default function SearchBar({ symbols, selected, onSearch }: { symbols: readonly string[]; selected: string; onSearch: (symbol: string) => void }) {
  const [query, setQuery] = useState(''), [open, setOpen] = useState(false), [highlighted, setHighlighted] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const matches = symbols.filter((symbol) => symbol.includes(query.trim().toUpperCase()))
  useEffect(() => { setHighlighted(0) }, [query])
  useEffect(() => { const close = (event: MouseEvent) => { if (!ref.current?.contains(event.target as Node)) setOpen(false) }; document.addEventListener('mousedown', close); return () => document.removeEventListener('mousedown', close) }, [])
  function choose(symbol: string) { onSearch(symbol); setQuery(''); setOpen(false) }
  function keyDown(event: KeyboardEvent<HTMLInputElement>) { if (event.key === 'ArrowDown') { event.preventDefault(); setHighlighted((value) => Math.min(value + 1, Math.max(matches.length - 1, 0))) } else if (event.key === 'ArrowUp') { event.preventDefault(); setHighlighted((value) => Math.max(value - 1, 0)) } else if (event.key === 'Enter' && matches[highlighted]) { event.preventDefault(); choose(matches[highlighted]) } else if (event.key === 'Escape') setOpen(false) }
  return <div className="search-wrap" ref={ref}><span className="search-icon" aria-hidden="true">⌕</span><input className="search-input" role="combobox" aria-label="Search supported stock symbol" aria-expanded={open} aria-controls="stock-suggestions" aria-autocomplete="list" placeholder={`Search supported stocks · ${selected}`} value={query} onFocus={() => setOpen(true)} onChange={(event) => { setQuery(event.target.value); setOpen(true) }} onKeyDown={keyDown} />{open && <div className="suggestions" id="stock-suggestions" role="listbox">{matches.length ? matches.map((symbol, index) => <button className={index === highlighted ? 'highlighted' : ''} key={symbol} type="button" role="option" aria-selected={selected === symbol} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(symbol)}>{symbol}</button>) : <span className="no-results">No supported stock found</span>}</div>}</div>
}
