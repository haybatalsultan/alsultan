document.addEventListener('DOMContentLoaded', () => {
  const hero = document.getElementById('home-hero');
  if (hero) {
    const slides = Array.from(hero.querySelectorAll('.hero-slide'));
    const dots = Array.from(hero.querySelectorAll('.hero-dots button'));
    const prev = hero.querySelector('.hero-prev');
    const next = hero.querySelector('.hero-next');
    let index = 0;
    const show = (newIndex) => {
      index = (newIndex + slides.length) % slides.length;
      slides.forEach((slide, i) => { slide.hidden = i !== index; slide.classList.toggle('active', i === index); });
      dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
    };
    if (slides.length > 1) {
      prev?.addEventListener('click', () => show(index - 1));
      next?.addEventListener('click', () => show(index + 1));
      dots.forEach((dot, i) => dot.addEventListener('click', () => show(i)));
    }
  }

  const locationButton = document.getElementById('use-location');
  if (!locationButton) return;
  const language = document.documentElement.lang || 'ar';
  locationButton.addEventListener('click', () => {
    if (!navigator.geolocation) {
      alert(language === 'en' ? 'Location services are not supported by this browser.' : 'خدمة الموقع غير مدعومة في هذا المتصفح.');
      return;
    }
    locationButton.disabled = true;
    navigator.geolocation.getCurrentPosition((position) => {
      const lat = document.getElementById('id_latitude');
      const lng = document.getElementById('id_longitude');
      if (lat) lat.value = position.coords.latitude.toFixed(6);
      if (lng) lng.value = position.coords.longitude.toFixed(6);
      locationButton.textContent = language === 'en' ? 'Location Added' : 'تمت إضافة الموقع';
      locationButton.disabled = false;
    }, () => {
      alert(language === 'en' ? 'We could not access your location. You can enter the address manually.' : 'تعذر الحصول على موقعك. يمكنك إدخال العنوان يدويًا.');
      locationButton.disabled = false;
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
  });
});

// Lightweight live viewer indicator. Presence is anonymous and refreshed at a
// modest interval to avoid unnecessary traffic. The server deduplicates the
// same browser session and expires stale viewers automatically.
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('product-viewers-form');
  const output = document.getElementById('product-live-viewers');
  if (!form || !output) return;

  const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
  const url = form.dataset.viewersUrl;
  const language = output.dataset.language || 'ar';
  if (!csrf || !url) return;

  const renderCount = (count) => {
    if (!Number.isInteger(count) || count < 2) {
      output.hidden = true;
      output.textContent = '';
      return;
    }
    if (language === 'en') {
      output.textContent = `👁 ${count} people are viewing this item now`;
    } else if (count === 2) {
      output.textContent = '👁 شخصان يشاهدان هذه القطعة الآن';
    } else {
      output.textContent = `👁 ${count} أشخاص يشاهدون هذه القطعة الآن`;
    }
    output.hidden = false;
  };

  const heartbeat = async () => {
    if (document.visibilityState !== 'visible') return;
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf,
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json',
        },
        credentials: 'same-origin',
        cache: 'no-store',
      });
      if (!response.ok) return;
      const data = await response.json();
      renderCount(Number(data.count));
    } catch (_) {
      // The viewer counter is non-critical UX; storefront purchasing must keep
      // working even when Redis/network access is temporarily unavailable.
    }
  };

  heartbeat();
  const timer = window.setInterval(heartbeat, 30000);
  window.addEventListener('pagehide', () => window.clearInterval(timer), { once: true });
});


// Responsive navigation usability: close the Bootstrap collapse after a
// navigation choice on compact screens, and support Escape without adding
// inline script or weakening CSP.
document.addEventListener('DOMContentLoaded', () => {
  const nav = document.getElementById('storeNav');
  const toggle = document.querySelector('[data-bs-target="#storeNav"]');
  if (!nav || !toggle) return;

  const closeNav = () => {
    if (window.innerWidth > 991 || !nav.classList.contains('show')) return;
    if (window.bootstrap?.Collapse) {
      window.bootstrap.Collapse.getOrCreateInstance(nav, { toggle: false }).hide();
    } else {
      nav.classList.remove('show');
      toggle.setAttribute('aria-expanded', 'false');
    }
  };

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', closeNav);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeNav();
  });
});
