import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { KnowledgeEditor } from './KnowledgeEditor';
import type { NoteDocument } from '../notes';

const fixture = JSON.parse(readFileSync(resolve('../backend/tests/fixtures/blocknote_v1.json'), 'utf8'));

it('renders and reconstructs real headings, toggles, code, nested lists, styles, links and image metadata', async () => {
  // JSDOM has no layout engine. These observers only support the real UI mount.
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} })));
  vi.stubGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
  const document = structuredClone(fixture.mixed) as NoteDocument;
  const image = document.find((block) => block.type === 'image')!;
  (image.props as { url: string }).url = '/api/assets/23d398da-6ac8-4e17-a6f0-1b8048714d2a';
  const changed = vi.fn();
  const rendered = render(<KnowledgeEditor noteId="local-test" initialDocument={document} onDocumentChange={changed} />);
  for (let level = 1; level <= 6; level++) {
    expect(await screen.findByRole('heading', { name: 'Heading ' + level })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Toggle ' + level })).toBeInTheDocument();
  }
  expect(rendered.container.querySelector('strong')).toHaveTextContent('All styles');
  expect(rendered.container.querySelector('em')).toHaveTextContent('All styles');
  expect(rendered.container.querySelector('u')).toHaveTextContent('All styles');
  expect(rendered.container.querySelector('s')).toHaveTextContent('All styles');
  expect(rendered.container.querySelector('p code')).toHaveTextContent('inline code');
  expect(rendered.container.querySelector('[data-content-type="quote"]')).toHaveTextContent('Quote');
  expect(screen.getByRole('link', { name: 'Reference' })).toHaveAttribute('href', 'https://example.invalid/evidence');
  expect(rendered.container.querySelector('[data-content-type="codeBlock"]')).toHaveTextContent('print("local 🚀")');
  expect(rendered.container.querySelector('[data-id="nested-list"] [data-id="deep-check"]')).toBeInTheDocument();
  expect(rendered.container.querySelector('img')).toHaveAttribute('src', (image.props as { url: string }).url);
  const toggle = rendered.container.querySelector('[data-id="case-toggle_heading_3"] .bn-toggle-button')!;
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  fireEvent.click(toggle); expect(toggle).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByText('Nested toggle body 3')).toBeInTheDocument();
  const checkbox = rendered.container.querySelector('[data-id="case-checkListItem"] input')!;
  expect(checkbox).toBeChecked(); fireEvent.click(checkbox);
  await waitFor(() => expect(changed).toHaveBeenCalled());
  const emitted = changed.mock.lastCall![0] as NoteDocument;
  expect(emitted.find((block) => block.id === 'case-checkListItem')!.props).toMatchObject({ checked: false });
  expect(emitted.find((block) => block.type === 'image')!.props).toEqual(image.props);
  rendered.unmount();
  const reopened = render(<KnowledgeEditor noteId="local-test" initialDocument={emitted} onDocumentChange={vi.fn()} />);
  expect(await screen.findByRole('heading', { name: 'Heading 6' })).toBeInTheDocument();
  expect(reopened.container.querySelector('[data-id="case-checkListItem"] input')).not.toBeChecked();
  expect(reopened.container.querySelector('[data-id="case-toggle_heading_3"] .bn-toggle-button')).toHaveAttribute('aria-expanded', 'true');
  expect(reopened.container.querySelector('img')).toHaveAttribute('src', (image.props as { url: string }).url);
});
