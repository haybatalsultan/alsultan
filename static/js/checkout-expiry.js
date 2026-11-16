(() => {
  'use strict';

  const root = document.querySelector('[data-checkout-expiry]');
  if (!root) return;

  const output = root.querySelector('[data-checkout-countdown]');
  const message = root.querySelector('[data-checkout-expiry-message]');
  const expiryRaw = root.dataset.expiresAt || '';
  const expiryMs = Date.parse(expiryRaw);
  if (!Number.isFinite(expiryMs)) return;

  let expired = false;
  let warned = false;

  const disablePaymentControls = () => {
    document.querySelectorAll('[data-reservation-payment-button]').forEach((button) => {
      button.disabled = true;
      button.setAttribute('aria-disabled', 'true');
    });
  };

  const format = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const tick = () => {
    const remaining = Math.max(0, Math.ceil((expiryMs - Date.now()) / 1000));
    if (output) output.textContent = format(remaining);

    if (remaining <= 300 && remaining > 0 && !warned) {
      warned = true;
      root.classList.add('is-warning');
      if (message) {
        message.textContent = document.documentElement.lang === 'en'
          ? 'Less than 5 minutes remain. Complete payment before the reservation expires.'
          : 'تبقى أقل من 5 دقائق. أكمل الدفع قبل انتهاء الحجز.';
      }
    }

    if (remaining === 0 && !expired) {
      expired = true;
      root.classList.remove('is-warning');
      root.classList.add('is-expired');
      disablePaymentControls();
      if (message) {
        message.textContent = document.documentElement.lang === 'en'
          ? 'Reservation expired. Refreshing securely releases the inventory.'
          : 'انتهت مهلة الحجز. يتم الآن تحديث الطلب وتحرير المخزون بأمان.';
      }
      // The browser never mutates inventory. Reloading calls the server-side
      // expiry routine, which owns the database lock and inventory release.
      window.setTimeout(() => {
        window.location.assign(root.dataset.expiredUrl || window.location.href);
      }, 900);
    }
  };

  tick();
  window.setInterval(tick, 1000);
})();
