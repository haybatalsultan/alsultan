(() => {
  'use strict';

  const button = document.querySelector('[data-copy-ambassador-code]');
  const codeNode = document.querySelector('[data-ambassador-code]');
  const statusNode = document.querySelector('[data-copy-status]');
  if (!button || !codeNode) return;

  const originalLabel = button.dataset.copyLabel || 'Copy';
  const copiedLabel = button.dataset.copiedLabel || 'Copied';
  const labelNode = button.querySelector('[data-copy-text]');

  const setFeedback = (message) => {
    if (labelNode) labelNode.textContent = message;
    if (statusNode) statusNode.textContent = message;
    window.setTimeout(() => {
      if (labelNode) labelNode.textContent = originalLabel;
      if (statusNode) statusNode.textContent = '';
    }, 1800);
  };

  button.addEventListener('click', async () => {
    const text = (codeNode.textContent || '').trim();
    if (!text) return;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        setFeedback(copiedLabel);
        return;
      }
      // Clipboard API requires a secure context. If unavailable, keep the code visible for manual copy.
      setFeedback(originalLabel);
    } catch (_) {
      // No sensitive data is logged. The code remains visible for manual copy.
    }
  });
})();
