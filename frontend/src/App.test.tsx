import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from './App';

// DOM unit tests cover shell/request behavior; the real editor is checked in a browser.
vi.mock('./components/KnowledgeEditor', () => ({
  KnowledgeEditor: () => <section aria-label="Note editor" />,
}));

describe('workspace health', () => {
  it('renders both panes and reports a healthy local backend', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ status: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);
    expect(screen.getByRole('complementary')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByLabelText('Note editor')).toBeInTheDocument();
    expect(await screen.findByText('Backend: online')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/health', expect.objectContaining({ signal: expect.any(AbortSignal) }));
  });

  it.each([
    ['network failure', () => Promise.reject(new Error('offline'))],
    ['HTTP failure', () => Promise.resolve({ ok: false })],
    ['wrong response', () => Promise.resolve({ ok: true, json: async () => ({ status: 'wrong' }) })],
  ])('keeps the shell available on %s', async (_name, response) => {
    vi.stubGlobal('fetch', vi.fn(response));
    render(<App />);
    expect(await screen.findByText('Backend: offline')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});
