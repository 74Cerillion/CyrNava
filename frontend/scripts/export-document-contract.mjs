// Run after a reviewed editor update; the test suite detects schema drift.
import { URL } from 'node:url';
import console from 'node:console';
import { readFile, writeFile } from 'node:fs/promises';
import { schema } from '../src/components/editorSchema.ts';

const installed = JSON.parse(await readFile(new URL('../node_modules/@blocknote/core/package.json', import.meta.url), 'utf8'));
const contract = { format_version: 1, blocknote_version: installed.version,
  blocks: schema.blockSchema, inline: schema.inlineContentSchema, styles: schema.styleSchema };
await writeFile(new URL('../../backend/app/document_format_v1.json', import.meta.url), JSON.stringify(contract, null, 2) + '\n');
console.log('Updated document format 1 contract. Review the diff and run compatibility tests.');
