(() => {
  "use strict";
  const root = document.querySelector("[data-receivable-payment]");
  if (!root) return;
  const form = root.querySelector(".receivable-payment-form");
  const amount = root.querySelector("#id_amount");
  const confirm = root.querySelector("#id_confirm_received");
  const submit = root.querySelector("[data-payment-submit]");
  const full = root.querySelector("[data-pay-full]");
  const paymentPreview = root.querySelector("[data-payment-preview]");
  const afterPreview = root.querySelector("[data-after-preview]");
  const outstanding = Number.parseFloat(root.dataset.outstanding || "0");

  const clampAmount = () => {
    const parsed = Number.parseFloat(amount.value);
    return Number.isFinite(parsed) ? Math.max(0, Math.min(parsed, outstanding)) : 0;
  };
  const fmt = (value) => Number(value).toLocaleString("en-AE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const refresh = () => {
    const payment = clampAmount();
    paymentPreview.textContent = fmt(payment);
    afterPreview.textContent = fmt(Math.max(0, outstanding - payment));
    submit.disabled = !(payment > 0 && payment <= outstanding && confirm.checked);
  };
  amount.addEventListener("input", refresh);
  confirm.addEventListener("change", refresh);
  full.addEventListener("click", () => {
    amount.value = outstanding.toFixed(2);
    amount.focus();
    refresh();
  });
  form.addEventListener("submit", () => {
    submit.disabled = true;
  });
  refresh();
})();
