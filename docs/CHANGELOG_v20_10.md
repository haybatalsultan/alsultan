# v20.10 TEST

## Smart customer tracking menu
- Adds Track My Order to desktop and mobile customer account menus only when active orders exist.
- One active order opens the customer's order directly; multiple active orders open My Orders.
- Delivered/cancelled/returned-only customers do not see the shortcut.

## Secure order email notifications
- Owner-only notification settings page.
- Configurable administration notification address with official store email fallback.
- Admin: new order, payment received, optional shipment/delivery notifications.
- Customer: payment confirmation and shipment/out-for-delivery/delivered notifications.
- Persistent unique OrderNotification records prevent duplicate email sends.
- SMTP failures cannot roll back orders/payments/inventory/status changes.
- No Stripe secrets, payment provider IDs, card data, or internal notes in messages.

## Migrations
- core.0003_store_notification_settings
- orders.0012_ordernotification
