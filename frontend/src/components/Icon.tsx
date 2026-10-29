// Small local UI glyphs; the authoritative emblem is always the supplied PNG.
const paths = {
  home: 'm3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9',
  folder: 'M3 6h7l2 3h9v11H3zM3 6V4h7l2 2',
  note: 'M5 3h10l4 4v14H5zM14 3v5h5M8 12h8M8 16h8',
  rename: 'm4 16-1 5 5-1L20 8l-4-4zM14 6l4 4',
  move: 'M3 12h17m-6-6 6 6-6 6',
  delete: 'M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7',
  refresh: 'M20 7v5h-5M4 17v-5h5M5 8a8 8 0 0 1 13-3l2 7M4 12l2 7a8 8 0 0 0 13-3',
  hide: 'm3 3 18 18M10 5h2c5 0 9 7 9 7a20 20 0 0 1-4 4M6 6a20 20 0 0 0-3 6s4 7 9 7h2M10 10a3 3 0 0 0 4 4',
  show: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12m7 0a3 3 0 1 0 6 0 3 3 0 0 0-6 0',
  templates: 'm12 2 10 6-10 6L2 8zM3 12l9 6 9-6M3 16l9 6 9-6',
  save: 'M5 3h10l4 4v14H5zM14 3v5h5M9 13h6M12 10v6',
  check: 'm5 12 4 4L19 6',
  warning: 'm12 3 10 18H2zM12 9v5m0 3v1',
} as const;
export type IconName = keyof typeof paths;
export function Icon({ name }: { name: IconName }) {
  return <svg className="ui-icon" aria-hidden="true" focusable="false" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]} /></svg>;
}
