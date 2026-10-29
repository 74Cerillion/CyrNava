/* global localStorage, matchMedia, document */
// Blocking, same-origin startup script: apply the preference before React/CSS paint.
// Release CSP disallows inline JavaScript; /assets is already served locally.
(() => {
  let preference = 'auto';
  let cyrnava = false;
  try {
    cyrnava = localStorage.getItem('cyrnava.theme.v1') === 'cyrnava';
    const stored = localStorage.getItem('engage.appearance.v1');
    if (stored === 'light' || stored === 'dark' || stored === 'auto') preference = stored;
  } catch { /* Storage failure still permits System appearance. */ }
  const dark = cyrnava || preference === 'dark' || (preference === 'auto'
    && typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.setAttribute('data-mantine-color-scheme', dark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-cyrnava-theme', String(cyrnava));
})();
