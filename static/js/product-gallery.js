'use strict';

document.addEventListener('DOMContentLoaded', () => {
  const gallery = document.getElementById('premium-product-gallery');
  if (!gallery) {
    return;
  }

  const main = gallery.querySelector('.premium-gallery-main');
  const thumbs = [...gallery.querySelectorAll('[data-gallery-index]')];
  const lightbox = gallery.querySelector('#premium-lightbox');
  const image = lightbox?.querySelector('.premium-lightbox-image');
  const viewport = lightbox?.querySelector('[data-gallery-viewport]');
  const counter = lightbox?.querySelector('[data-gallery-counter]');

  if (!main || !lightbox || !image || !viewport) {
    return;
  }

  const items = thumbs.length
    ? thumbs.map((element) => ({
        detail: element.dataset.detailSrc,
        zoom: element.dataset.zoomSrc,
        alt: element.dataset.alt || '',
      }))
    : [
        {
          detail: main.src,
          zoom: main.dataset.zoomSrc || main.src,
          alt: main.alt || '',
        },
      ];

  let index = 0;
  let scale = 1;
  let x = 0;
  let y = 0;
  let dragging = false;
  let startX = 0;
  let startY = 0;
  let baseX = 0;
  let baseY = 0;
  let touchX = null;

  const clamp = (number, minimum, maximum) =>
    Math.min(maximum, Math.max(minimum, number));

  const applyTransform = () => {
    image.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`;
  };

  const resetZoom = () => {
    scale = 1;
    x = 0;
    y = 0;
    applyTransform();
  };

  const select = (newIndex) => {
    index = (newIndex + items.length) % items.length;
    const item = items[index];
    main.src = item.detail;
    main.dataset.zoomSrc = item.zoom;
    main.alt = item.alt;
    thumbs.forEach((thumb, thumbIndex) => {
      thumb.classList.toggle('is-active', thumbIndex === index);
    });
  };

  const showLightboxImage = () => {
    const item = items[index];
    resetZoom();
    image.src = item.zoom;
    image.alt = item.alt;
    if (counter) {
      counter.textContent = `${index + 1} / ${items.length}`;
    }
  };

  const open = () => {
    showLightboxImage();
    lightbox.hidden = false;
    document.body.classList.add('gallery-open');
    lightbox.querySelector('[data-gallery-close]')?.focus();
  };

  const close = () => {
    lightbox.hidden = true;
    document.body.classList.remove('gallery-open');
    resetZoom();
  };

  const move = (step) => {
    index = (index + step + items.length) % items.length;
    select(index);
    showLightboxImage();
  };

  const zoom = (delta) => {
    scale = clamp(scale + delta, 1, 4);
    if (scale === 1) {
      x = 0;
      y = 0;
    }
    applyTransform();
  };

  thumbs.forEach((thumb, thumbIndex) => {
    thumb.addEventListener('click', () => select(thumbIndex));
  });

  gallery.querySelector('[data-gallery-open]')?.addEventListener('click', open);
  gallery.querySelectorAll('[data-gallery-close]').forEach((element) => {
    element.addEventListener('click', close);
  });
  gallery
    .querySelector('[data-gallery-prev]')
    ?.addEventListener('click', () => move(-1));
  gallery
    .querySelector('[data-gallery-next]')
    ?.addEventListener('click', () => move(1));
  gallery
    .querySelector('[data-gallery-zoom-in]')
    ?.addEventListener('click', () => zoom(0.5));
  gallery
    .querySelector('[data-gallery-zoom-out]')
    ?.addEventListener('click', () => zoom(-0.5));

  viewport.addEventListener('dblclick', () => {
    if (scale === 1) {
      zoom(1);
    } else {
      resetZoom();
    }
  });

  viewport.addEventListener(
    'wheel',
    (event) => {
      if (lightbox.hidden) {
        return;
      }
      event.preventDefault();
      zoom(event.deltaY < 0 ? 0.25 : -0.25);
    },
    { passive: false },
  );

  viewport.addEventListener('pointerdown', (event) => {
    if (scale <= 1) {
      return;
    }
    dragging = true;
    startX = event.clientX;
    startY = event.clientY;
    baseX = x;
    baseY = y;
    viewport.setPointerCapture?.(event.pointerId);
  });

  viewport.addEventListener('pointermove', (event) => {
    if (!dragging) {
      return;
    }
    x = baseX + (event.clientX - startX);
    y = baseY + (event.clientY - startY);
    applyTransform();
  });

  viewport.addEventListener('pointerup', () => {
    dragging = false;
  });

  viewport.addEventListener(
    'touchstart',
    (event) => {
      if (event.touches.length === 1) {
        touchX = event.touches[0].clientX;
      }
    },
    { passive: true },
  );

  viewport.addEventListener(
    'touchend',
    (event) => {
      if (touchX === null || scale > 1) {
        return;
      }
      const endX = event.changedTouches[0]?.clientX ?? touchX;
      const distance = endX - touchX;
      touchX = null;
      if (Math.abs(distance) > 50) {
        move(distance > 0 ? -1 : 1);
      }
    },
    { passive: true },
  );

  document.addEventListener('keydown', (event) => {
    if (lightbox.hidden) {
      return;
    }
    if (event.key === 'Escape') {
      close();
    }
    if (event.key === 'ArrowLeft') {
      move(document.documentElement.dir === 'rtl' ? 1 : -1);
    }
    if (event.key === 'ArrowRight') {
      move(document.documentElement.dir === 'rtl' ? -1 : 1);
    }
    if (event.key === '+') {
      zoom(0.5);
    }
    if (event.key === '-') {
      zoom(-0.5);
    }
  });
});
