import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { GlobalSearch } from './GlobalSearch';
import { searchNotes } from '../search';
import type { SearchResponse } from '../search';

vi.mock('../search', () => ({ searchNotes: vi.fn() }));
const result: SearchResponse = { query: 'enum', total: 2, results: [
  { note_id: 'one', title: 'Enumeration', folder_path: ['Lab', 'Discovery'], snippet: 'nmap enumeration', score: -2 },
  { note_id: 'two', title: 'Code', folder_path: [], snippet: 'enumerate_services()', score: -1 },
] };
beforeEach(() => { vi.resetAllMocks(); vi.useFakeTimers(); vi.mocked(searchNotes).mockResolvedValue(result); });
afterEach(() => vi.useRealTimers());
async function tick(ms = 300) { await act(async () => { await vi.advanceTimersByTimeAsync(ms); }); }
function setup() {
  const open = vi.fn(); const view = render(<GlobalSearch disabled={false} refreshVersion={0} onOpen={open} />);
  return { ...view, open, query: screen.getByRole('combobox', { name: 'Search all notes' }) };
}

it('debounces for 300ms and never searches an empty/whitespace field', async () => {
  const { query } = setup(); await tick(500); expect(searchNotes).not.toHaveBeenCalled();
  fireEvent.change(query, { target: { value: '   ' } }); await tick(); expect(searchNotes).not.toHaveBeenCalled();
  fireEvent.change(query, { target: { value: 'en' } }); await tick(250);
  fireEvent.change(query, { target: { value: 'enum' } }); await tick(299);
  expect(searchNotes).not.toHaveBeenCalled(); expect(screen.getByText('Waiting to search...')).toBeInTheDocument();
  await tick(1); expect(searchNotes).toHaveBeenCalledExactlyOnceWith('enum', expect.any(AbortSignal));
  expect(screen.getAllByRole('option')).toHaveLength(2);
});
it('shows loading, folder paths, bounded-result count and safely highlighted text', async () => {
  let finish!: (value: SearchResponse) => void;
  vi.mocked(searchNotes).mockReturnValue(new Promise((resolve) => { finish = resolve; }));
  const { query, container } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  expect(screen.getByText('Searching...')).toBeInTheDocument();
  await act(async () => finish({ ...result, total: 25, results: [result.results[0], {
    ...result.results[1], snippet: '<script>enum</script><img src=x onerror=bad()>',
  }] }));
  expect(screen.getByText('Lab / Discovery')).toBeInTheDocument(); expect(screen.getByText('Workspace root')).toBeInTheDocument();
  expect(screen.getByText(/Showing 2 of 25/)).toBeInTheDocument();
  expect(container.querySelector('mark')).toHaveTextContent('Enum');
  expect(container.querySelector('script, img')).toBeNull();
  expect(container.textContent).toContain('<script>enum</script><img src=x onerror=bad()>');
});
it('uses local arrow/Enter navigation, wraps selection and clears with Escape', async () => {
  const { query, open } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  fireEvent.keyDown(query, { key: 'ArrowDown' });
  expect(screen.getAllByRole('option')[0]).toHaveAttribute('aria-selected', 'true');
  expect(query).toHaveAttribute('aria-activedescendant', screen.getAllByRole('option')[0].id);
  fireEvent.keyDown(query, { key: 'ArrowDown' }); fireEvent.keyDown(query, { key: 'Enter' });
  expect(open).toHaveBeenLastCalledWith('two');
  fireEvent.keyDown(query, { key: 'ArrowDown' }); fireEvent.keyDown(query, { key: 'ArrowUp' });
  expect(screen.getAllByRole('option')[1]).toHaveAttribute('aria-selected', 'true');
  fireEvent.keyDown(query, { key: 'Escape' }); expect(query).toHaveValue(''); expect(query).toHaveFocus();
  expect(screen.queryByRole('option')).not.toBeInTheDocument(); expect(query).toHaveAttribute('aria-expanded', 'false');
});
it('clicks a result and defaults Enter to the first match without changing query', async () => {
  const { query, open } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  fireEvent.keyDown(query, { key: 'Enter' }); expect(open).toHaveBeenLastCalledWith('one');
  fireEvent.click(screen.getAllByRole('option')[1]); expect(open).toHaveBeenLastCalledWith('two'); expect(query).toHaveValue('enum');
});
it('immediately aborts and hides superseded results; late successes cannot replace a newer query', async () => {
  const pending: ((value: SearchResponse) => void)[] = [];
  vi.mocked(searchNotes).mockImplementation(() => new Promise((resolve) => pending.push(resolve)));
  const { query } = setup(); fireEvent.change(query, { target: { value: 'old' } }); await tick();
  const oldSignal = vi.mocked(searchNotes).mock.calls[0][1]!;
  fireEvent.change(query, { target: { value: 'new' } }); expect(oldSignal.aborted).toBe(true);
  await act(async () => pending[0](result)); expect(screen.queryByRole('option')).not.toBeInTheDocument();
  await tick(); await act(async () => pending[1]({ query: 'new', total: 1, results: [result.results[1]] }));
  expect(screen.getAllByRole('option')).toHaveLength(1); expect(screen.getByRole('option')).toHaveAccessibleName('Open note: Code');
});
it('ignores a late failure/success after clear, including a backend ignoring abort', async () => {
  let fail!: (error: Error) => void;
  vi.mocked(searchNotes).mockReturnValue(new Promise((_, reject) => { fail = reject; }));
  const { query } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  fireEvent.click(screen.getByRole('button', { name: 'Clear search' }));
  await act(async () => fail(new Error('Late failure')));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument(); expect(query).toHaveValue('');
});
it('keeps the newer results when the oldest request completes last', async () => {
  const pending: ((value: SearchResponse) => void)[] = [];
  vi.mocked(searchNotes).mockImplementation(() => new Promise((resolve) => pending.push(resolve)));
  const { query } = setup(); fireEvent.change(query, { target: { value: 'old' } }); await tick();
  fireEvent.change(query, { target: { value: 'new' } }); await tick();
  await act(async () => pending[1]({ query: 'new', total: 1, results: [result.results[1]] }));
  await act(async () => pending[0](result));
  expect(screen.getAllByRole('option')).toHaveLength(1);
  expect(screen.getByRole('option')).toHaveAccessibleName('Open note: Code');
  expect(screen.queryByText('Searching...')).not.toBeInTheDocument();
});
it.each(['clear', 'other query'])('does not resurrect cached results when returning to the same term after %s', async (action) => {
  const { query } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  expect(screen.getAllByRole('option')).toHaveLength(2);
  if (action === 'clear') fireEvent.click(screen.getByRole('button', { name: 'Clear search' }));
  else fireEvent.change(query, { target: { value: 'other' } });
  fireEvent.change(query, { target: { value: 'enum' } });
  expect(screen.queryByRole('option')).not.toBeInTheDocument();
  expect(screen.getByText('Waiting to search...')).toBeInTheDocument();
  await tick(); expect(screen.getAllByRole('option')).toHaveLength(2);
});
it('clears with Escape from retry/clear controls and does not restore an old error for the same term', async () => {
  vi.mocked(searchNotes).mockRejectedValueOnce(new Error('Old error')).mockResolvedValue(result);
  const { query, open } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  const retry = screen.getByRole('button', { name: 'Retry search' }); retry.focus(); fireEvent.keyDown(retry, { key: 'Escape' });
  expect(query).toHaveValue(''); expect(query).toHaveFocus();
  fireEvent.change(query, { target: { value: 'enum' } }); expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  await tick(); const clear = screen.getByRole('button', { name: 'Clear search' }); clear.focus();
  const enter = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true });
  clear.dispatchEvent(enter); expect(enter.defaultPrevented).toBe(false); expect(open).not.toHaveBeenCalled();
  fireEvent.keyDown(clear, { key: 'Escape' }); expect(query).toHaveValue(''); expect(query).toHaveFocus();
});
it('shows errors and retries without losing the query; empty results have a clear message', async () => {
  vi.mocked(searchNotes).mockRejectedValueOnce(new Error('Local backend offline')).mockResolvedValueOnce({ query: 'enum', total: 0, results: [] });
  const { query } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  expect(screen.getByRole('alert')).toHaveTextContent('Local backend offline'); expect(query).toHaveValue('enum');
  fireEvent.click(screen.getByRole('button', { name: 'Retry search' })); await tick();
  expect(screen.getByText('No matching notes.')).toBeInTheDocument(); expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
it('refreshes the same query after committed changes and rejects the preceding response', async () => {
  let finish!: (value: SearchResponse) => void;
  vi.mocked(searchNotes).mockResolvedValueOnce(result).mockReturnValueOnce(new Promise((resolve) => { finish = resolve; }));
  const { query, rerender, open } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  rerender(<GlobalSearch disabled={false} refreshVersion={1} onOpen={open} />);
  expect(screen.queryByRole('option')).not.toBeInTheDocument(); await tick();
  rerender(<GlobalSearch disabled={false} refreshVersion={2} onOpen={open} />);
  await act(async () => finish(result)); expect(screen.queryByRole('option')).not.toBeInTheDocument();
  vi.mocked(searchNotes).mockResolvedValue({ query: 'enum', total: 0, results: [] }); await tick();
  expect(screen.getByText('No matching notes.')).toBeInTheDocument();
});
it('does not intercept composition or activate locked results, and cancels on unmount', async () => {
  const { query, open, rerender, unmount } = setup(); fireEvent.change(query, { target: { value: 'enum' } }); await tick();
  fireEvent.keyDown(query, { key: 'Enter', isComposing: true }); expect(open).not.toHaveBeenCalled();
  rerender(<GlobalSearch disabled={true} refreshVersion={0} onOpen={open} />);
  expect(query).toBeDisabled(); fireEvent.keyDown(query, { key: 'Enter' }); fireEvent.click(screen.getAllByRole('option')[0]);
  expect(open).not.toHaveBeenCalled(); const signal = vi.mocked(searchNotes).mock.calls[0][1]!;
  unmount(); expect(signal.aborted).toBe(true);
});
