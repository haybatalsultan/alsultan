(() => {
  'use strict';

  const ajaxHeaders = { 'X-Requested-With': 'XMLHttpRequest' };
  let miniCartTimer = null;

  const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  const cartCountNodes = () => document.querySelectorAll('[data-cart-count]');
  const cartIconNode = () => document.querySelector('[data-cart-icon]');
  const isMobileViewport = () => window.matchMedia?.('(max-width: 767px)').matches;

  function setCartCount(value) {
    const count = Math.max(0, Number(value) || 0);
    cartCountNodes().forEach((node) => {
      node.textContent = String(count);
      node.classList.toggle('is-empty', count < 1);
      node.classList.remove('cart-count-pop');
      node.getBoundingClientRect();
      node.classList.add('cart-count-pop');
    });
    const icon = cartIconNode();
    if (icon) {
      icon.classList.remove('cart-icon-pop');
      icon.getBoundingClientRect();
      icon.classList.add('cart-icon-pop');
    }
  }

  function setWishlistCount(value) {
    const count = Math.max(0, Number(value) || 0);
    document.querySelectorAll('[data-wishlist-count]').forEach((node) => {
      node.textContent = String(count);
      node.classList.toggle('is-empty', count < 1);
    });
    document.querySelectorAll('[data-wishlist-header], [data-wishlist-mobile]').forEach((node) => {
      node.classList.toggle('has-items', count > 0);
    });
  }

  function showMiniCart(data) {
    const panel = document.querySelector('[data-mini-cart]');
    if (!panel) return;
    const lang = document.documentElement.lang || 'ar';
    const name = lang.startsWith('en') ? data.product_name_en : data.product_name_ar;
    panel.querySelector('[data-mini-cart-name]').textContent = name || data.product_sku || '';
    panel.querySelector('[data-mini-cart-qty]').textContent = String(data.quantity || 1);
    panel.querySelector('[data-mini-cart-total]').textContent = data.unit_price || '0.00';

    const media = panel.querySelector('[data-mini-cart-media]');
    media.replaceChildren();
    if (data.image_url) {
      const image = document.createElement('img');
      image.src = data.image_url;
      image.alt = '';
      media.appendChild(image);
    } else {
      const fallback = document.createElement('span');
      fallback.textContent = 'HS';
      media.appendChild(fallback);
    }

    panel.hidden = false;
    requestAnimationFrame(() => panel.classList.add('is-visible'));
    window.clearTimeout(miniCartTimer);
    miniCartTimer = window.setTimeout(() => {
      panel.classList.remove('is-visible');
      window.setTimeout(() => { panel.hidden = true; }, reducedMotion() ? 0 : 220);
    }, 4200);
  }

  let mobileSheetCloseTimer = null;
  let mobileSheetPreviousFocus = null;

  function closeMobileCartSheet() {
    const sheet = document.querySelector('[data-mobile-cart-sheet]');
    const backdrop = document.querySelector('[data-mobile-cart-backdrop]');
    if (!sheet || !backdrop) return;
    sheet.classList.remove('is-visible');
    backdrop.classList.remove('is-visible');
    window.clearTimeout(mobileSheetCloseTimer);
    mobileSheetCloseTimer = window.setTimeout(() => {
      sheet.hidden = true;
      backdrop.hidden = true;
      document.body.classList.remove('cart-sheet-open');
      mobileSheetPreviousFocus?.focus?.({ preventScroll: true });
      mobileSheetPreviousFocus = null;
    }, reducedMotion() ? 0 : 240);
  }

  function ensureMobileCartSheet() {
    let sheet = document.querySelector('[data-mobile-cart-sheet]');
    let backdrop = document.querySelector('[data-mobile-cart-backdrop]');
    if (sheet && backdrop) return { sheet, backdrop };

    const lang = document.documentElement.lang || 'ar';
    const isEnglish = lang.startsWith('en');

    backdrop = document.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'mobile-cart-backdrop';
    backdrop.hidden = true;
    backdrop.setAttribute('aria-label', isEnglish ? 'Close cart preview' : 'إغلاق معاينة السلة');
    backdrop.dataset.mobileCartBackdrop = '';

    sheet = document.createElement('section');
    sheet.className = 'mobile-cart-sheet';
    sheet.hidden = true;
    sheet.dataset.mobileCartSheet = '';
    sheet.setAttribute('role', 'dialog');
    sheet.setAttribute('aria-modal', 'true');
    sheet.setAttribute('aria-labelledby', 'mobile-cart-sheet-title');

    const handle = document.createElement('span');
    handle.className = 'mobile-cart-sheet__handle';
    handle.setAttribute('aria-hidden', 'true');

    const head = document.createElement('div');
    head.className = 'mobile-cart-sheet__head';
    const titleWrap = document.createElement('div');
    const eyebrow = document.createElement('small');
    eyebrow.textContent = isEnglish ? 'Added successfully' : 'تمت الإضافة بنجاح';
    const title = document.createElement('strong');
    title.id = 'mobile-cart-sheet-title';
    title.textContent = isEnglish ? 'Your cart' : 'سلتك';
    titleWrap.append(eyebrow, title);

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'mobile-cart-sheet__close';
    close.dataset.mobileCartClose = '';
    close.setAttribute('aria-label', isEnglish ? 'Close' : 'إغلاق');
    close.textContent = '×';
    head.append(titleWrap, close);

    const product = document.createElement('div');
    product.className = 'mobile-cart-sheet__product';
    const media = document.createElement('div');
    media.className = 'mobile-cart-sheet__media';
    media.dataset.mobileCartMedia = '';
    const copy = document.createElement('div');
    copy.className = 'mobile-cart-sheet__copy';
    const name = document.createElement('strong');
    name.dataset.mobileCartName = '';
    const meta = document.createElement('span');
    meta.dataset.mobileCartMeta = '';
    copy.append(name, meta);
    product.append(media, copy);

    const actions = document.createElement('div');
    actions.className = 'mobile-cart-sheet__actions';
    const continueButton = document.createElement('button');
    continueButton.type = 'button';
    continueButton.className = 'mobile-cart-sheet__continue';
    continueButton.dataset.mobileCartClose = '';
    continueButton.textContent = isEnglish ? 'Continue shopping' : 'متابعة التسوق';
    const cartLink = document.createElement('a');
    cartLink.className = 'mobile-cart-sheet__cart-link';
    cartLink.href = '/orders/cart/';
    cartLink.textContent = isEnglish ? 'View cart' : 'عرض السلة';
    actions.append(continueButton, cartLink);

    sheet.append(handle, head, product, actions);
    document.body.append(backdrop, sheet);
    return { sheet, backdrop };
  }

  function showMobileCartSheet(data) {
    if (!isMobileViewport()) return;
    const { sheet, backdrop } = ensureMobileCartSheet();
    const lang = document.documentElement.lang || 'ar';
    const name = lang.startsWith('en') ? data.product_name_en : data.product_name_ar;
    sheet.querySelector('[data-mobile-cart-name]').textContent = name || data.product_sku || '';
    sheet.querySelector('[data-mobile-cart-meta]').textContent = `${data.quantity || 1} × AED ${data.unit_price || '0.00'}`;

    const media = sheet.querySelector('[data-mobile-cart-media]');
    media.replaceChildren();
    if (data.image_url) {
      const image = document.createElement('img');
      image.src = data.image_url;
      image.alt = '';
      image.loading = 'lazy';
      media.appendChild(image);
    } else {
      const fallback = document.createElement('span');
      fallback.textContent = 'HS';
      media.appendChild(fallback);
    }

    mobileSheetPreviousFocus = document.activeElement;
    window.clearTimeout(mobileSheetCloseTimer);
    backdrop.hidden = false;
    sheet.hidden = false;
    document.body.classList.add('cart-sheet-open');
    requestAnimationFrame(() => {
      backdrop.classList.add('is-visible');
      sheet.classList.add('is-visible');
      sheet.querySelector('[data-mobile-cart-close]')?.focus({ preventScroll: true });
    });
  }

  function animateProductToCart(card) {
    if (reducedMotion()) return;
    const source = card?.querySelector('.product-card-image, .detail-image img, .detail-image');
    const target = cartIconNode();
    if (!source || !target) return;

    const from = source.getBoundingClientRect();
    const to = target.getBoundingClientRect();
    if (!from.width || !to.width) return;

    const flyer = source.cloneNode(true);
    flyer.className = 'cart-flyer';
    flyer.setAttribute('aria-hidden', 'true');
    Object.assign(flyer.style, {
      left: `${from.left}px`,
      top: `${from.top}px`,
      width: `${Math.min(from.width, 120)}px`,
      height: `${Math.min(from.height, 120)}px`,
    });
    document.body.appendChild(flyer);

    const x = (to.left + to.width / 2) - (from.left + Math.min(from.width, 120) / 2);
    const y = (to.top + to.height / 2) - (from.top + Math.min(from.height, 120) / 2);
    const animation = flyer.animate([
      { transform: 'translate3d(0,0,0) scale(1)', opacity: 0.95, offset: 0 },
      { transform: `translate3d(${x * 0.55}px, ${y * 0.35 - 40}px, 0) scale(.72) rotate(-5deg)`, opacity: 0.9, offset: 0.58 },
      { transform: `translate3d(${x}px, ${y}px, 0) scale(.12) rotate(8deg)`, opacity: 0.12, offset: 1 },
    ], { duration: 720, easing: 'cubic-bezier(.2,.75,.22,1)' });
    animation.addEventListener('finish', () => flyer.remove(), { once: true });
    animation.addEventListener('cancel', () => flyer.remove(), { once: true });
  }

  async function postForm(form) {
    const response = await fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: ajaxHeaders,
      credentials: 'same-origin',
    });
    let data = {};
    try { data = await response.json(); } catch (_) { /* fall through */ }
    if (!response.ok || data.ok === false) {
      throw new Error(data.message || 'Unable to update the cart.');
    }
    return data;
  }

  function setButtonBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
    button.classList.toggle('is-loading', busy);
    button.setAttribute('aria-busy', busy ? 'true' : 'false');
  }

  function showCartToast(message, type = 'error', options = {}) {
    const toast = document.createElement('div');
    toast.className = `cart-toast cart-toast--${type}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');

    const icon = document.createElement('span');
    icon.className = 'cart-toast__icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = type === 'success' ? '✓' : type === 'info' ? 'i' : '!';

    const copy = document.createElement('span');
    copy.className = 'cart-toast__copy';
    copy.textContent = message;

    toast.append(icon, copy);

    if (options.actionUrl && options.actionLabel) {
      const action = document.createElement('a');
      action.className = 'cart-toast__action';
      action.href = options.actionUrl;
      action.textContent = options.actionLabel;
      toast.appendChild(action);
    }

    if (options.mobileProminent && isMobileViewport()) {
      toast.classList.add('cart-toast--mobile-prominent');
    }

    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('is-visible'));
    window.setTimeout(() => {
      toast.classList.remove('is-visible');
      window.setTimeout(() => toast.remove(), reducedMotion() ? 0 : 200);
    }, 3600);
  }

  function markAddButtonAtStockLimit(button) {
    if (!button) return;
    const lang = document.documentElement.lang || 'ar';
    const label = button.querySelector('[data-add-label]');
    if (label) label.textContent = lang.startsWith('en') ? 'In cart' : '✓ في السلة';
    button.classList.add('is-in-cart');
    button.disabled = true;
    button.setAttribute('aria-disabled', 'true');
  }

  document.addEventListener('submit', async (event) => {
    const wishlistForm = event.target.closest('[data-wishlist-toggle]');
    if (wishlistForm) {
      event.preventDefault();
      const button = wishlistForm.querySelector('[data-wishlist-button]');
      const label = wishlistForm.querySelector('[data-wishlist-label]');
      setButtonBusy(button, true);
      try {
        const data = await postForm(wishlistForm);
        const wishlisted = Boolean(data.wishlisted);
        const lang = document.documentElement.lang || 'ar';
        button?.classList.toggle('is-wishlisted', wishlisted);
        button?.setAttribute('aria-pressed', wishlisted ? 'true' : 'false');
        setWishlistCount(data.wishlist_count);
        const isEnglish = lang.startsWith('en');
        let accessibleText;
        let visibleText;
        let toastText;
        if (wishlisted) {
          accessibleText = isEnglish ? 'Remove from wishlist' : 'إزالة من المفضلة';
          visibleText = isEnglish ? 'Remove from Wishlist' : 'إزالة من المفضلة';
          toastText = isEnglish ? 'Added to your wishlist.' : 'تمت الإضافة إلى المفضلة.';
        } else {
          accessibleText = isEnglish ? 'Add to wishlist' : 'إضافة إلى المفضلة';
          visibleText = isEnglish ? 'Add to Wishlist' : 'إضافة إلى المفضلة';
          toastText = isEnglish ? 'Removed from your wishlist.' : 'تمت الإزالة من المفضلة.';
        }
        if (button) {
          button.setAttribute('aria-label', accessibleText);
          button.setAttribute('title', accessibleText);
        }
        if (label) {
          label.textContent = visibleText;
        }
        showCartToast(data.message || toastText, 'success');
      } catch (error) {
        showCartToast(error.message, 'error');
      } finally {
        setButtonBusy(button, false);
      }
      return;
    }

    const addForm = event.target.closest('[data-add-to-cart]');
    if (addForm) {
      event.preventDefault();
      const button = addForm.querySelector('[data-add-button]');
      const card = addForm.closest('[data-product-card]');
      setButtonBusy(button, true);
      try {
        const data = await postForm(addForm);
        setCartCount(data.cart_count);
        animateProductToCart(card || addForm.closest('.product-detail-page'));
        const lang = document.documentElement.lang || 'ar';
        if (!isMobileViewport()) {
          showMiniCart(data);
        } else {
          showMobileCartSheet(data);
        }
        button?.classList.add('is-added');
        showCartToast(
          lang.startsWith('en')
            ? `${data.product_sku || 'Item'} was added to your cart. Stock is reserved only at payment.`
            : `تمت إضافة ${data.product_sku || 'القطعة'} إلى السلة. يبدأ الحجز عند مرحلة الدفع فقط.`,
          'success',
          {
            actionUrl: '/orders/cart/',
            actionLabel: lang.startsWith('en') ? 'View cart' : 'عرض السلة',
            mobileProminent: true,
          },
        );
        if (data.stock_limit_reached) {
          markAddButtonAtStockLimit(button);
        } else {
          window.setTimeout(() => button?.classList.remove('is-added'), 1200);
        }
      } catch (error) {
        // The server remains authoritative for stock and quantity validation.
        showCartToast(error.message, 'error');
      } finally {
        setButtonBusy(button, false);
      }
      return;
    }

    const removeForm = event.target.closest('[data-cart-remove-form]');
    if (removeForm) {
      event.preventDefault();
      const row = removeForm.closest('[data-cart-row]');
      const button = removeForm.querySelector('button');
      setButtonBusy(button, true);
      try {
        const data = await postForm(removeForm);
        setCartCount(data.cart_count);
        if (data.cart_empty) {
          window.location.reload();
          return;
        }
        row?.classList.add('is-removing');
        window.setTimeout(() => row?.remove(), reducedMotion() ? 0 : 260);
        updateCartTotal(data.grand_total);
      } catch (error) {
        showCartToast(error.message, 'error');
        setButtonBusy(button, false);
      }
      return;
    }

    const quantityForm = event.target.closest('[data-cart-quantity-form]');
    if (quantityForm) {
      event.preventDefault();
      await submitQuantity(quantityForm);
    }
  });

  function updateCartTotal(value) {
    document.querySelectorAll('[data-cart-grand-total]').forEach((node) => {
      node.textContent = value || '0.00';
    });
  }

  async function submitQuantity(form) {
    const input = form.querySelector('[data-qty-input]');
    const row = form.closest('[data-cart-row]');
    const controls = form.querySelectorAll('button, input');
    controls.forEach((control) => { control.disabled = true; });
    try {
      const data = await postForm(form);
      input.value = data.quantity;
      row?.querySelector('[data-line-total]')?.replaceChildren(document.createTextNode(data.line_total));
      setCartCount(data.cart_count);
      updateCartTotal(data.grand_total);
      row?.classList.add('is-updated');
      window.setTimeout(() => row?.classList.remove('is-updated'), 450);
    } catch (error) {
      showCartToast(error.message, 'error');
      window.location.reload();
    } finally {
      controls.forEach((control) => { control.disabled = false; });
    }
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-mobile-cart-close], [data-mobile-cart-backdrop]')) {
      closeMobileCartSheet();
      return;
    }
    const minus = event.target.closest('[data-qty-minus]');
    const plus = event.target.closest('[data-qty-plus]');
    if (!minus && !plus) return;
    const form = event.target.closest('[data-cart-quantity-form]');
    const input = form?.querySelector('[data-qty-input]');
    if (!form || !input) return;
    const min = Number(input.min || 1);
    const max = Number(input.max || 10);
    const current = Number(input.value || 1);
    const next = minus ? Math.max(min, current - 1) : Math.min(max, current + 1);
    if (next === current) return;
    input.value = String(next);
    form.requestSubmit();
  });

  document.addEventListener('change', (event) => {
    const input = event.target.closest('[data-qty-input]');
    if (!input) return;
    const min = Number(input.min || 1);
    const max = Number(input.max || 10);
    const value = Math.min(max, Math.max(min, Number(input.value || min)));
    input.value = String(value);
    input.closest('form')?.requestSubmit();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && document.querySelector('[data-mobile-cart-sheet].is-visible')) {
      closeMobileCartSheet();
    }
  });

  function formatReservation(seconds) {
    const safe = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(safe / 60);
    const secs = safe % 60;
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  async function expireCartRow(row) {
    if (!row || row.dataset.expirePending === '1') return;
    row.dataset.expirePending = '1';
    row.classList.add('is-expiring');
    const form = row.querySelector('[data-cart-expire-form]');
    if (!form) {
      window.location.reload();
      return;
    }
    try {
      const data = await postForm(form);
      if (!data.expired) {
        row.dataset.expirePending = '0';
        row.classList.remove('is-expiring');
        row.dataset.reservationSeconds = String(data.remaining_seconds || 0);
        return;
      }
      setCartCount(data.cart_count);
      updateCartTotal(data.grand_total);
      const lang = document.documentElement.lang || 'ar';
      showCartToast(lang.startsWith('en')
        ? 'The reservation expired and the item was removed from your cart.'
        : 'انتهت مدة حجز القطعة وتمت إزالتها من السلة.', 'info');
      window.setTimeout(() => window.location.reload(), 450);
    } catch (_) {
      // Server remains authoritative; a reload reconciles any concurrent expiry.
      window.location.reload();
    }
  }

  function startReservationCountdowns() {
    document.querySelectorAll('[data-cart-row][data-reservation-seconds]').forEach((row) => {
      const timer = row.querySelector('[data-reservation-timer]');
      const clock = row.querySelector('[data-reservation-clock]');
      if (!timer || !clock) return;
      let remaining = Math.max(0, Number(row.dataset.reservationSeconds) || 0);
      const started = performance.now();
      let intervalId = null;
      const render = () => {
        const elapsed = Math.floor((performance.now() - started) / 1000);
        const seconds = Math.max(0, remaining - elapsed);
        clock.textContent = formatReservation(seconds);
        timer.classList.toggle('is-warning', seconds > 0 && seconds <= 300);
        timer.classList.toggle('is-critical', seconds > 0 && seconds <= 60);
        if (seconds <= 0) {
          if (intervalId) window.clearInterval(intervalId);
          expireCartRow(row);
        }
      };
      render();
      if (remaining > 0) intervalId = window.setInterval(render, 1000);
    });
  }

  startReservationCountdowns();

  function startLiveCartReconciliation() {
    const root = document.querySelector('[data-cart-live-status-url]');
    if (!root) return;
    const url = root.dataset.cartLiveStatusUrl;
    let currentCount = Number(root.dataset.cartLiveCount || 0);
    const check = async () => {
      if (document.hidden) return;
      try {
        const sep = url.includes('?') ? '&' : '?';
        const response = await fetch(`${url}${sep}count=${encodeURIComponent(currentCount)}`, {
          credentials: 'same-origin',
          headers: {'X-Requested-With': 'XMLHttpRequest'},
          cache: 'no-store',
        });
        if (!response.ok) return;
        const data = await response.json();
        if (data.changed) {
          const lang = document.documentElement.lang || 'ar';
          showCartToast(lang.startsWith('en')
            ? 'Your cart changed because one or more items are no longer available.'
            : 'تم تحديث سلتك لأن قطعة أو أكثر لم تعد متاحة.', 'info');
          window.setTimeout(() => window.location.reload(), 500);
          return;
        }
        currentCount = Number(data.cart_count || 0);
      } catch (_) {
        // Non-critical UX reconciliation. Server-side checkout remains authoritative.
      }
    };
    window.setInterval(check, 20000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); });
  }

  startLiveCartReconciliation();

})();
