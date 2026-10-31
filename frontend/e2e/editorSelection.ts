import { expect } from '@playwright/test';
import type { Locator } from '@playwright/test';
import type { EditorView } from '@tiptap/pm/view';

// Read-only test diagnostics. TipTap attaches its editor to the contenteditable
// DOM node for tests; no application bridge or production activation flag.
export async function editorSelection(editor: Locator) {
  return editor.evaluate((element) => {
    const view = (element as HTMLElement & { editor?: { view: EditorView } }).editor?.view;
    if (!view || view.dom !== element) throw new Error('Expected the mounted editor view');
    const selection = window.getSelection();
    const point = (node: Node | null, offset: number) => {
      const target = node instanceof Element ? node : node?.parentElement;
      const block = target?.closest('[data-content-type]');
      const inside = !!node && element.contains(node);
      return {
        node: node?.nodeName ?? null, offset,
        position: inside ? view.posAtDOM(node!, offset) : null,
        blockType: block?.getAttribute('data-content-type') ?? null,
        blockId: block?.closest('[data-id]')?.getAttribute('data-id') ?? null,
      };
    };
    const anchor = point(selection?.anchorNode ?? null, selection?.anchorOffset ?? 0);
    const focus = point(selection?.focusNode ?? null, selection?.focusOffset ?? 0);
    const model = view.state.selection;
    const ancestors = Array.from({ length: model.$from.depth + 1 }, (_, depth) => {
      const node = model.$from.node(depth);
      return { type: node.type.name, id: typeof node.attrs.id === 'string' ? node.attrs.id : null };
    });
    const blockId = [...ancestors].reverse().find((node) => node.id)?.id ?? null;
    return {
      activeElement: { tag: document.activeElement?.tagName, role: document.activeElement?.getAttribute('role'), editor: document.activeElement === element },
      dom: { anchor, focus, collapsed: selection?.isCollapsed === true },
      model: { type: model.constructor.name, from: model.from, to: model.to, parent: model.$from.parent.type.name,
        parentOffset: model.$from.parentOffset, contentSize: model.$from.parent.content.size, blockId, ancestors },
      synchronized: model.anchor === anchor.position && model.head === focus.position,
      blocks: Array.from(element.querySelectorAll('[data-content-type]')).map((node) => ({
        type: node.getAttribute('data-content-type'), id: node.closest('[data-id]')?.getAttribute('data-id') ?? null,
        imageLoaded: node.querySelector('img') instanceof HTMLImageElement && (node.querySelector('img') as HTMLImageElement).naturalWidth > 0,
      })),
    };
  });
}

export async function paragraphCursor(editor: Locator, options: { blockId?: string; empty?: boolean } = {}) {
  // Keyboard commands use the editor model, while a click can move the DOM caret
  // first. Require agreement instead of assuming click completion implies it.
  await expect.poll(async () => {
    const state = await editorSelection(editor);
    return { focused: state.activeElement.editor, collapsed: state.dom.collapsed,
      synchronized: state.synchronized, parent: state.model.parent, domParent: state.dom.anchor.blockType,
      sameBlock: state.model.blockId === state.dom.anchor.blockId,
      ...(options.blockId ? { blockId: state.model.blockId } : {}),
      ...(options.empty ? { contentSize: state.model.contentSize } : {}),
    };
  }, { message: 'Wait for a focused, collapsed paragraph cursor shared by DOM and editor model' }).toEqual({
    focused: true, collapsed: true, synchronized: true, parent: 'paragraph', domParent: 'paragraph', sameBlock: true,
    ...(options.blockId ? { blockId: options.blockId } : {}), ...(options.empty ? { contentSize: 0 } : {}),
  });
}
