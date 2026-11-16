from django.urls import path

from . import views, webhooks

app_name = "orders"
urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/status/", views.cart_status, name="cart_status"),
    path("cart/add/<uuid:public_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("cart/beads/<int:item_id>/", views.cart_bead_adjustment, name="cart_bead_adjustment"),
    path("cart/quantity/<int:item_id>/", views.cart_quantity, name="cart_quantity"),
    path("cart/expire/<int:item_id>/", views.cart_expire, name="cart_expire"),
    path("cart/follow-up/", views.cart_follow_up, name="cart_follow_up"),
    path(
        "cart/follow-up/cancel/",
        views.cart_follow_up_cancel,
        name="cart_follow_up_cancel",
    ),
    path(
        "cart/reservation-limit-request/",
        views.reservation_limit_request,
        name="reservation_limit_request",
    ),
    path("checkout/", views.checkout, name="checkout"),
    path("track/", views.track_order, name="track"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("confirmation/<uuid:public_id>/", views.confirmation, name="confirmation"),
    path(
        "payment/stripe/start/<uuid:public_id>/",
        views.stripe_payment_start,
        name="stripe_payment_start",
    ),
    path(
        "payment/manual/start/<uuid:public_id>/",
        views.manual_payment_start,
        name="manual_payment_start",
    ),
    path(
        "payment/stripe/success/<uuid:public_id>/",
        views.stripe_payment_success,
        name="payment_success",
    ),
    path("payment/stripe/webhook/", webhooks.stripe_webhook, name="stripe_webhook"),
    path("<uuid:public_id>/", views.order_detail, name="detail"),
]
