import { useEffect, useId, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { searchNotes } from '../search';
import type { SearchResponse } from '../search';
import { Icon } from './Icon';

interface Props {
  disabled: boolean;
  refreshVersion: number;
  onOpen: (noteId: string) => void;
}
type SearchState = { key: string } & (
  { kind: 'loading' } | { kind: 'ready'; data: SearchResponse } | { kind: 'error'; message: string }
);

function Highlight({ text, query }: { text: string; query: string }) {
  const words = [...new Set(query.match(/[\p{L}\p{N}]+/gu) || [])];
  if (!words.length) return text;
  // Query words contain only letters/numbers. Matches are React text nodes,
  // never HTML. Highlighting is approximate; FTS remains the matching authority.
  const pattern = new RegExp(`(?<![\\p{L}\\p{N}])(${words.sort((a, b) => b.length - a.length).join('|')})`, 'giu');
  return text.split(pattern).map((part, index) => index % 2 ? <mark key={index}>{part}</mark> : part);
}

export function GlobalSearch({ disabled, refreshVersion, onOpen }: Props) {
  const [query, setQuery] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<SearchState | null>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const input = useRef<HTMLInputElement>(null);
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const id = useId();
  const term = query.trim();
  const key = JSON.stringify([term, refreshVersion, attempt]);

  useEffect(() => {
    if (!term) return;
    const controller = new AbortController();
    request.current = controller;
    const current = ++generation.current;
    const timer = window.setTimeout(async () => {
      setState({ key, kind: 'loading' });
      try {
        const data = await searchNotes(term, controller.signal);
        if (controller.signal.aborted || current !== generation.current) return;
        setState({ key, kind: 'ready', data }); setActiveIndex(-1);
      } catch (error) {
        // http.ts converts cancellation to ApiError; inspect our signal instead.
        if (controller.signal.aborted || current !== generation.current) return;
        setState({ key, kind: 'error', message: error instanceof Error ? error.message : 'Try again.' });
      }
    }, 300);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [term, key]);

  function invalidate() { ++generation.current; request.current?.abort(); setState(null); setActiveIndex(-1); }
  function changeQuery(value: string) {
    if (value.trim() !== term) invalidate();
    setQuery(value);
  }
  function clear() { invalidate(); setQuery(''); input.current?.focus(); }

  // Hide old results immediately, including during debounce and after a saved
  // note/folder change. A late old response cannot become an actionable result.
  const current = term && state?.key === key ? state : null;
  const ready = current?.kind === 'ready' ? current.data : null;
  const results = ready?.results || [];
  const selected = activeIndex >= 0 && activeIndex < results.length ? activeIndex : -1;
  function handleKey(event: KeyboardEvent<HTMLElement>) {
    if (disabled || event.nativeEvent.isComposing) return;
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); clear(); }
    if (['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key) && results.length) {
      event.preventDefault(); event.stopPropagation();
      if (event.key === 'Enter') onOpen(results[selected < 0 ? 0 : selected].note_id);
      else {
        const next = event.key === 'ArrowDown' ? (selected + 1) % results.length
          : selected <= 0 ? results.length - 1 : selected - 1;
        setActiveIndex(next); input.current?.focus();
        document.getElementById(`${id}-result-${next}`)?.scrollIntoView?.({ block: 'nearest' });
      }
    }
  }

  return <section className="global-search" aria-label="Global note search"
    onKeyDown={(event) => { if (event.key === 'Escape') handleKey(event); }}>
    <label htmlFor={`${id}-input`}>Search all notes</label>
    <div className="search-controls">
      <div className="search-input"><Icon name="search" />
        <input id={`${id}-input`} ref={input} role="combobox" type="search" autoComplete="off" maxLength={200}
          placeholder="Search all notes..." value={query} disabled={disabled}
          aria-expanded={ready !== null} aria-controls={ready ? `${id}-results` : undefined}
          aria-autocomplete="list" aria-describedby={`${id}-help`}
          aria-activedescendant={selected < 0 ? undefined : `${id}-result-${selected}`}
          onChange={(event) => changeQuery(event.target.value)} onKeyDown={handleKey} />
      </div>
      {query && <button type="button" className="secondary" disabled={disabled} onClick={clear}>Clear search</button>}
    </div>
    <p className="hint search-help" id={`${id}-help`}>Search saved notes. ↑ ↓ select; Enter opens; Esc clears.</p>
    <p role="status" className="search-status" aria-live="polite">
      {!term ? '' : current?.kind === 'error' ? '' : !current ? 'Waiting to search...' : current.kind === 'loading' ? 'Searching...'
        : ready?.total === 0 ? 'No matching notes.' : ready && ready.total > results.length
          ? `Showing ${results.length} of ${ready.total} matching notes. Refine your search for more.`
          : `${ready?.total} matching ${ready?.total === 1 ? 'note' : 'notes'}.`}
    </p>
    {current?.kind === 'error' && <div role="alert"><p>Search unavailable. {current.message}</p>
      <button type="button" className="secondary" disabled={disabled} onClick={() => { invalidate(); setAttempt((value) => value + 1); }}>Retry search</button>
    </div>}
    {ready && <ul id={`${id}-results`} role="listbox" aria-label="Search results" className="search-results">
      {results.map((result, index) => <li role="presentation" key={result.note_id}>
        <button id={`${id}-result-${index}`} type="button" role="option" aria-label={`Open note: ${result.title}`}
          aria-describedby={`${id}-path-${index} ${id}-snippet-${index}`}
          aria-selected={selected === index} tabIndex={-1} disabled={disabled} className="search-result"
          onMouseDown={(event) => event.preventDefault()}
          onKeyDown={(event) => { if (event.key !== 'Enter' && event.key !== ' ') handleKey(event); }}
          onClick={() => onOpen(result.note_id)}>
          <strong><Highlight text={result.title} query={term} /></strong>
          <span id={`${id}-path-${index}`} className="search-path">{result.folder_path.length ? result.folder_path.join(' / ') : 'Workspace root'}</span>
          <span id={`${id}-snippet-${index}`} className="search-snippet"><Highlight text={result.snippet} query={term} /></span>
        </button>
      </li>)}
    </ul>}
  </section>;
}
