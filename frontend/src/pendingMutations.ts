// Tracks completed HTTP mutations, including template dialogs outside the note.
// Bodies and credentials are never retained here.
let pending = 0;
let failures = 0;
export function beginMutation(): (success: boolean) => void {
  pending++;
  let finished = false;
  return (success) => { if (!finished) { finished = true; pending--; if (!success) failures++; } };
}
export function mutationState() { return { pending, failures }; }
export async function waitForMutations(deadline: number): Promise<void> {
  while (pending) {
    if (Date.now() >= deadline) throw new Error('Pending changes did not finish.');
    await new Promise((resolve) => window.setTimeout(resolve, 20));
  }
}
