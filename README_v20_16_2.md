# v20.16.2 — Management Shell + Order Status Filter SECURITY TEST

- Dedicated management header for `/management/` pages; storefront cart/wishlist/navigation/footer are not rendered there.
- Management navigation is permission-aware and remains backed by existing `staff_required` / `require_permission` checks.
- Responsive offcanvas management navigation for mobile.
- Server-side allowlisted order status filter using `Order.Status.choices`; search + stage + status pagination state is preserved.
- Management orders table becomes stacked mobile cards below 768px.
- Notification settings checkboxes redesigned as compact responsive toggle cards.
- Management pages skip customer-only cart/wishlist/tracking context DB lookups.
- No model or migration changes.
