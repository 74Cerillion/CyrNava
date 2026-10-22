import { expect, it } from 'vitest';
import { ancestorIds, visibleRows } from './tree';
import type { DirectoryData } from './library';

it('traverses a deep folder chain iteratively without a call-stack limit', () => {
  const data: DirectoryData = { folders: [], notes: [] };
  for (let index = 0; index < 2000; index++) data.folders.push({
    id: String(index), parent_id: index === 0 ? null : String(index - 1), name: `Folder ${index}`,
    sort_order: 0, created_at: '', updated_at: '',
  });
  const rows = visibleRows(data, new Set(), true);
  expect(rows).toHaveLength(2000);
  expect(rows[1999].depth).toBe(1999);
  expect(ancestorIds(data, '1999')).toHaveLength(2000);
});
