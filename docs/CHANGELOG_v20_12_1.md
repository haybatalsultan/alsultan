# v20.12.1 — Timed Cart Reservation Compatibility Fix

- Preserves timed server-side cart reservations introduced in v20.12.
- Converts legacy/null-deadline CartItem rows into a real reservation at checkout under database locks.
- Does not extend an already active reservation deadline.
- Restores AJAX `free_quantity` semantics to mean the total quantity still available to the current cart (global free stock + the cart's own reservation).
- Keeps stock-limit UI behavior for unique pieces.
- No model or migration changes.
