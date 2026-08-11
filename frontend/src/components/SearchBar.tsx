import { useState } from 'react'
import type { FormEvent } from 'react'

export default function SearchBar({ onSearch }: { onSearch: (symbol: string) => void }) {
  const [query, setQuery] = useState('')
  function submit(event: FormEvent) { event.preventDefault(); const value = query.trim().toUpperCase(); if (value) { onSearch(value); setQuery('') } }
  return <form className="search-wrap" onSubmit={submit}><span className="search-icon" aria-hidden="true">⌕</span><input className="search-input" aria-label="Search stock symbol" placeholder="Search symbol" value={query} onChange={(event) => setQuery(event.target.value)} /></form>
}
