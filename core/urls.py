from django.urls import path

from ambassadors import management_views as am

from . import management_views as m
from . import views

app_name = "core"
urlpatterns = [
    path(
        "location/reverse/",
        views.reverse_geocode_location,
        name="reverse_geocode_location",
    ),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("robots.txt", views.robots, name="robots"),
    path("about/", views.about, name="about"),
    path("digital-services/", views.digital_services, name="digital_services"),
    path("coming-soon/<slug:slug>/", views.coming_soon, name="coming_soon"),
    path("info/<slug:slug>/", views.info_page, name="info"),
    path("management/", m.dashboard, name="management_dashboard"),
    path("management/search/", m.management_search, name="management_search"),
    path("management/quick-sale/", m.quick_sale, name="management_quick_sale"),
    path("management/receivables/", m.receivables, name="management_receivables"),
    path("management/receivables/<uuid:public_id>/payment/", m.receivable_payment, name="management_receivable_payment"),
    path("management/orders/<uuid:public_id>/invoice/create/", m.invoice_create, name="management_invoice_create"),
    path("management/invoices/<uuid:public_id>/", m.invoice_detail, name="management_invoice"),
    path("management/invoices/<uuid:public_id>/pdf/", m.invoice_pdf, name="management_invoice_pdf"),
    path("management/products/<uuid:public_id>/custody/", m.product_custody, name="management_product_custody"),
    path(
        "management/quick-sale/products/",
        m.quick_sale_product_search,
        name="management_quick_sale_product_search",
    ),
    path(
        "management/quick-sale/<uuid:public_id>/success/",
        m.quick_sale_success,
        name="management_quick_sale_success",
    ),
    path(
        "management/smart-accountant/",
        m.smart_accountant,
        name="management_smart_accountant",
    ),
    path("management/expenses/", m.expenses, name="management_expenses"),
    path(
        "management/expenses/add/", m.expense_create, name="management_expense_create"
    ),
    path(
        "management/expenses/<uuid:public_id>/edit/",
        m.expense_edit,
        name="management_expense_edit",
    ),
    path(
        "management/expenses/<uuid:public_id>/void/",
        m.expense_void,
        name="management_expense_void",
    ),
    path(
        "management/payment-settings/",
        m.payment_settings,
        name="management_payment_settings",
    ),
    path(
        "management/invoice-settings/",
        m.invoice_settings,
        name="management_invoice_settings",
    ),
    path(
        "management/notification-settings/",
        m.notification_settings,
        name="management_notification_settings",
    ),
    path(
        "management/checkout-fields/",
        m.checkout_field_settings,
        name="management_checkout_field_settings",
    ),
    path(
        "management/reservation-overrides/",
        m.reservation_overrides,
        name="management_reservation_overrides",
    ),
    path("management/ambassadors/", am.dashboard, name="management_ambassadors"),
    path(
        "management/ambassadors/toggle/",
        am.toggle,
        name="management_ambassadors_toggle",
    ),
    path(
        "management/ambassadors/referrals/<int:referral_id>/review/",
        am.review_referral,
        name="management_ambassador_referral_review",
    ),
    path("management/master-data/", m.master_data, name="management_master_data"),
    path(
        "management/master-data/categories/", m.categories, name="management_categories"
    ),
    path(
        "management/master-data/categories/create/",
        m.category_create,
        name="management_category_create",
    ),
    path(
        "management/master-data/categories/<uuid:public_id>/edit/",
        m.category_edit,
        name="management_category_edit",
    ),
    path(
        "management/master-data/categories/<uuid:public_id>/toggle/",
        m.category_toggle,
        name="management_category_toggle",
    ),
    path("management/master-data/materials/", m.materials, name="management_materials"),
    path(
        "management/master-data/materials/create/",
        m.material_create,
        name="management_material_create",
    ),
    path(
        "management/master-data/materials/<uuid:public_id>/edit/",
        m.material_edit,
        name="management_material_edit",
    ),
    path(
        "management/master-data/materials/<uuid:public_id>/toggle/",
        m.material_toggle,
        name="management_material_toggle",
    ),
    path("management/promotions/", m.promotions, name="management_promotions"),
    path(
        "management/promotions/create/",
        m.promotion_create,
        name="management_promotion_create",
    ),
    path(
        "management/promotions/<uuid:public_id>/edit/",
        m.promotion_edit,
        name="management_promotion_edit",
    ),
    path(
        "management/promotions/<uuid:public_id>/toggle/",
        m.promotion_toggle,
        name="management_promotion_toggle",
    ),
    path("management/products/", m.products, name="management_products"),
    path(
        "management/products/create/",
        m.product_create,
        name="management_product_create",
    ),
    path(
        "management/products/<uuid:public_id>/edit/",
        m.product_edit,
        name="management_product_edit",
    ),
    path(
        "management/products/<uuid:public_id>/images/",
        m.product_images,
        name="management_product_images",
    ),
    path(
        "management/products/<uuid:public_id>/images/<uuid:image_public_id>/update/",
        m.product_image_update,
        name="management_product_image_update",
    ),
    path(
        "management/products/<uuid:public_id>/images/<uuid:image_public_id>/primary/",
        m.product_image_primary,
        name="management_product_image_primary",
    ),
    path(
        "management/products/<uuid:public_id>/images/<uuid:image_public_id>/delete/",
        m.product_image_delete,
        name="management_product_image_delete",
    ),
    path(
        "management/products/<uuid:public_id>/pricing/",
        m.pricing,
        name="management_pricing",
    ),
    path(
        "management/products/<uuid:public_id>/pricing/history/",
        m.product_pricing_history,
        name="management_product_pricing_history",
    ),
    path(
        "management/products/<uuid:public_id>/pricing/clear-discount/",
        m.clear_direct_discount,
        name="management_clear_direct_discount",
    ),
    path(
        "management/products/pricing/clear-all-direct-discounts/",
        m.clear_all_direct_discounts,
        name="management_clear_all_direct_discounts",
    ),
    path(
        "management/products/<uuid:public_id>/inventory/",
        m.inventory_adjust,
        name="management_inventory_adjust",
    ),
    path("management/orders/", m.orders_list, name="management_orders"),
    path(
        "management/orders/<uuid:public_id>/", m.order_manage, name="management_order"
    ),
    path("management/customers/", m.customers, name="management_customers"),
    path("management/supervisors/", m.supervisors, name="management_supervisors"),
    path(
        "management/supervisors/create/",
        m.supervisor_create,
        name="management_supervisor_create",
    ),
    path(
        "management/supervisors/<uuid:public_id>/permissions/",
        m.supervisor_permissions,
        name="management_supervisor_permissions",
    ),
    path("management/audit/", m.audit_logs, name="management_audit"),
    path(
        "management/audit/<int:pk>/", m.audit_log_detail, name="management_audit_detail"
    ),
    path(
        "management/incomplete-carts/",
        m.abandoned_carts,
        name="management_abandoned_carts",
    ),
    path("management/bead-adjustment-settings/", m.bead_adjustment_settings, name="management_bead_adjustment_settings"),
]
