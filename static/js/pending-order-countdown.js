(() => {
  'use strict';
  const rows = [...document.querySelectorAll('[data-pending-order-expiry]')];
  if (!rows.length) return;
  const fmt = (seconds) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  let reloading = false;
  const tick = () => {
    const now = Date.now();
    for (const row of rows) {
      const expiry = Date.parse(row.dataset.pendingOrderExpiry || '');
      if (!Number.isFinite(expiry)) continue;
      const remaining = Math.max(0, Math.ceil((expiry - now) / 1000));
      const out = row.querySelector('[data-pending-countdown]');
      if (out) out.textContent = fmt(remaining);
      row.classList.toggle('is-critical', remaining > 0 && remaining <= 60);
      if (remaining === 0 && !reloading) {
        reloading = true;
        window.setTimeout(() => window.location.reload(), 900);
      }
    }
  };
  tick();
  window.setInterval(tick, 1000);
})();
