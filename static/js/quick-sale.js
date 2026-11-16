(() => {
  "use strict";

  const form = document.querySelector("[data-quick-sale]");
  if (!form) return;

  const search = form.querySelector("[data-product-search]");
  const results = form.querySelector("[data-product-results]");
  const status = form.querySelector("[data-search-status]");
  const spinner = form.querySelector("[data-search-spinner]");
  const productSelect = form.querySelector("#id_product");
  const selectedCard = form.querySelector("[data-selected-card]");
  const selectedImage = form.querySelector("[data-selected-image]");
  const discountInput = form.querySelector("#id_special_discount");
  const ack = form.querySelector("[data-sale-ack]");
  const submit = form.querySelector("[data-sale-submit]");
  const lang = (form.dataset.lang || "ar").toLowerCase();
  const endpoint = form.dataset.searchUrl;
  let current = null;
  let timer = null;
  let controller = null;

  const text = {
    ar: {
      searching: "جاري البحث…",
      empty: "لا توجد قطع متوفرة مطابقة للبحث.",
      error: "تعذر البحث حاليًا. حاول مرة أخرى.",
      available: "متوفر",
      select: "اختيار",
      none: "لا يوجد",
      inspected: "تم فحص المنتج",
      certified: "يوجد شهادة",
      confirm: "تأكيد البيع",
    },
    en: {
      searching: "Searching…",
      empty: "No available items match your search.",
      error: "Search is temporarily unavailable. Please try again.",
      available: "Available",
      select: "Select",
      none: "None",
      inspected: "Product inspected",
      certified: "Certified",
      confirm: "Confirm Sale",
    },
  }[lang.startsWith("en") ? "en" : "ar"];

  const money = (value) => {
    const number = Number.parseFloat(value);
    return Number.isFinite(number) ? Math.max(0, number) : 0;
  };
  const fmt = (value) => money(value).toLocaleString("en-AE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  function clearResults() {
    while (results.firstChild) results.removeChild(results.firstChild);
  }

  function safeText(el, value) {
    el.textContent = value == null || value === "" ? "—" : String(value);
  }

  function verificationLabel(code) {
    if (code === "CERTIFIED") return text.certified;
    if (code === "INSPECTED") return text.inspected;
    return text.none;
  }

  function updateSummary() {
    const price = current ? money(current.price) : 0;
    const discount = money(discountInput ? discountInput.value : 0);
    const total = Math.max(0, price - discount);
    safeText(form.querySelector("[data-summary-price]"), fmt(price));
    safeText(form.querySelector("[data-summary-discount]"), fmt(discount));
    safeText(form.querySelector("[data-summary-total]"), fmt(total));
    const submitTotal = form.querySelector("[data-submit-total]");
    submitTotal.textContent = current ? ` — ${fmt(total)} AED` : "";
    submit.disabled = !(current && ack.checked && total > 0);
  }

  function chooseProduct(product) {
    current = product;
    productSelect.value = String(product.id);
    selectedCard.hidden = false;
    safeText(form.querySelector("[data-selected-code]"), product.sku || product.reference);
    safeText(form.querySelector("[data-selected-name]"), lang.startsWith("en") ? product.name_en : product.name_ar);
    safeText(form.querySelector("[data-selected-material]"), lang.startsWith("en") ? product.material_en : product.material_ar);
    safeText(form.querySelector("[data-selected-beads]"), product.bead_count);
    safeText(form.querySelector("[data-selected-size]"), product.bead_size_mm ? `${product.bead_size_mm} mm` : "—");
    safeText(form.querySelector("[data-selected-weight]"), product.weight_g ? `${product.weight_g} g` : "—");
    safeText(form.querySelector("[data-selected-verification]"), verificationLabel(product.verification_status));
    safeText(form.querySelector("[data-selected-price]"), fmt(product.price));
    if (product.image_url && /^https:\/\//i.test(product.image_url)) {
      selectedImage.src = product.image_url;
      selectedImage.alt = lang.startsWith("en") ? product.name_en : product.name_ar;
      selectedImage.hidden = false;
    } else {
      selectedImage.removeAttribute("src");
      selectedImage.hidden = true;
    }
    clearResults();
    status.textContent = "";
    updateSummary();
  }

  function productCard(product) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "quick-sale-result-card";
    card.addEventListener("click", () => chooseProduct(product));

    const media = document.createElement("span");
    media.className = "quick-sale-result-media";
    if (product.image_url && /^https:\/\//i.test(product.image_url)) {
      const img = document.createElement("img");
      img.src = product.image_url;
      img.alt = lang.startsWith("en") ? product.name_en : product.name_ar;
      img.loading = "lazy";
      media.appendChild(img);
    }

    const copy = document.createElement("span");
    copy.className = "quick-sale-result-copy";
    const code = document.createElement("small");
    code.textContent = product.sku || product.reference;
    const name = document.createElement("strong");
    name.textContent = lang.startsWith("en") ? product.name_en : product.name_ar;
    const price = document.createElement("b");
    price.textContent = `${fmt(product.price)} AED`;
    copy.append(code, name, price);

    const badge = document.createElement("span");
    badge.className = "quick-sale-result-badge";
    badge.textContent = text.select;

    card.append(media, copy, badge);
    return card;
  }

  async function runSearch() {
    const q = search.value.trim().slice(0, 80);
    if (controller) controller.abort();
    controller = new AbortController();
    spinner.hidden = false;
    status.textContent = text.searching;

    try {
      const url = new URL(endpoint, window.location.origin);
      if (q) url.searchParams.set("q", q);
      const response = await fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers: {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("search_failed");
      const data = await response.json();
      clearResults();
      const items = Array.isArray(data.results) ? data.results.slice(0, 10) : [];
      items.forEach((product) => results.appendChild(productCard(product)));
      status.textContent = items.length ? "" : text.empty;
    } catch (error) {
      if (error.name !== "AbortError") {
        clearResults();
        status.textContent = text.error;
      }
    } finally {
      spinner.hidden = true;
    }
  }

  search.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(runSearch, 260);
  });
  search.addEventListener("focus", () => {
    if (!results.childElementCount) runSearch();
  });
  discountInput?.addEventListener("input", updateSummary);
  ack.addEventListener("change", updateSummary);
  form.querySelector("[data-change-product]")?.addEventListener("click", () => {
    current = null;
    productSelect.value = "";
    selectedCard.hidden = true;
    ack.checked = false;
    updateSummary();
    search.focus();
    runSearch();
  });

  // If a bound POST comes back invalid, preserve the selected server-side value,
  // but still require an explicit fresh selection before enabling confirmation.
  updateSummary();
})();

// v20.8.1.2 — deferred payment fields are display-only; Django revalidates them.
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-quick-sale]");
  if (!form) return;
  const method = form.querySelector("#id_payment_method");
  const fields = form.querySelector("[data-deferred-fields]");
  if (!method || !fields) return;
  const sync = () => { fields.hidden = method.value !== "DEFERRED"; };
  method.addEventListener("change", sync);
  sync();
});
