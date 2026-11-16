from inspect import unwrap
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from accounts import views as account_views
from ambassadors import views as ambassador_views
from core import management_views
from orders import views as order_views


class RequestFactoryMixin:
    @staticmethod
    def request(method="POST", *, post=None, get=None, user=None):
        return SimpleNamespace(
            method=method,
            POST=post or {},
            GET=get or {},
            FILES={},
            LANGUAGE_CODE="en",
            user=user or SimpleNamespace(role="OWNER", is_authenticated=True),
            session={},
            headers={},
        )


class CoreManagementNewCodeCoverageTests(RequestFactoryMixin, SimpleTestCase):
    def test_expense_edit_success_redirect(self):
        request = self.request()
        expense = SimpleNamespace(
            category="OPS",
            description="Office",
            amount=10,
            incurred_on=SimpleNamespace(isoformat=lambda: "2026-09-12"),
            supplier="Supplier",
            invoice_reference="INV-1",
            order_id=None,
            order=None,
            status=management_views.Expense.Status.ACTIVE,
        )
        updated = SimpleNamespace(**expense.__dict__)
        updated.save = MagicMock()
        form = MagicMock()
        form.is_valid.return_value = True
        form.save.return_value = updated
        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "get_object_or_404", return_value=expense),
            patch.object(management_views, "ExpenseForm", return_value=form),
            patch.object(management_views, "audit"),
            patch.object(management_views.messages, "success"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.expense_edit)(request, "expense-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_EXPENSES_URL)

    def test_expense_void_already_voided_redirect(self):
        request = self.request()
        expense = SimpleNamespace(status=management_views.Expense.Status.VOIDED)
        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "get_object_or_404", return_value=expense),
            patch.object(management_views.messages, "info"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.expense_void)(request, "expense-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_EXPENSES_URL)

    def test_category_edit_success_and_get_render_paths(self):
        category = SimpleNamespace(
            name_ar="تصنيف",
            name_en="Category",
            is_active=True,
            sort_order=1,
            image_public_id="img",
            slug="category",
            image_url="https://example.invalid/category.jpg",
        )
        updated = SimpleNamespace(**category.__dict__)
        form = MagicMock()
        form.is_valid.return_value = True
        request = self.request()
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=category),
            patch.object(management_views, "CategoryManagementForm", return_value=form),
            patch.object(management_views, "_save_master_data_form", return_value=updated),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.category_edit)(request, "category-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_CATEGORIES_URL)

        get_request = self.request(method="GET")
        get_form = MagicMock()
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=category),
            patch.object(management_views, "CategoryManagementForm", return_value=get_form),
            patch.object(management_views, "render", return_value="rendered") as render_mock,
        ):
            response = unwrap(management_views.category_edit)(get_request, "category-id")
        self.assertEqual(response, "rendered")
        self.assertEqual(render_mock.call_args.args[1], management_views.MANAGEMENT_FORM_TEMPLATE)

    def test_material_edit_success_and_get_render_paths(self):
        material = SimpleNamespace(
            name_ar="خامة",
            name_en="Material",
            is_active=True,
            sort_order=1,
            image_public_id="img",
            slug="material",
            image_url="https://example.invalid/material.jpg",
        )
        updated = SimpleNamespace(**material.__dict__)
        form = MagicMock()
        form.is_valid.return_value = True
        request = self.request()
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=material),
            patch.object(management_views, "MaterialManagementForm", return_value=form),
            patch.object(management_views, "_save_master_data_form", return_value=updated),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.material_edit)(request, "material-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_MATERIALS_URL)

        get_request = self.request(method="GET")
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=material),
            patch.object(management_views, "MaterialManagementForm", return_value=MagicMock()),
            patch.object(management_views, "render", return_value="rendered") as render_mock,
        ):
            response = unwrap(management_views.material_edit)(get_request, "material-id")
        self.assertEqual(response, "rendered")
        self.assertEqual(render_mock.call_args.args[1], management_views.MANAGEMENT_FORM_TEMPLATE)

    def test_material_toggle_redirect(self):
        request = self.request()
        material = SimpleNamespace(is_active=True, save=MagicMock())
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=material),
            patch.object(management_views.transaction, "atomic", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: False)),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.material_toggle)(request, "material-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_MATERIALS_URL)

    def test_product_image_redirect_paths(self):
        request = self.request(post={})
        product = SimpleNamespace(public_id="product-id")
        image = SimpleNamespace(
            public_id="image-id",
            alt_text_ar="ar",
            alt_text_en="en",
            sort_order=1,
        )

        invalid_form = MagicMock()
        invalid_form.is_valid.return_value = False
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", side_effect=[product, image]),
            patch.object(management_views, "ProductImageMetadataForm", return_value=invalid_form),
            patch.object(management_views, "redirect", return_value="invalid") as redirect_mock,
        ):
            response = unwrap(management_views.product_image_update)(request, "product-id", "image-id")
        self.assertEqual(response, "invalid")
        redirect_mock.assert_called_once_with(
            management_views.MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id
        )

        valid_form = MagicMock()
        valid_form.is_valid.return_value = True
        valid_form.cleaned_data = {"alt_text_ar": "ar2", "alt_text_en": "en2", "sort_order": 2}
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", side_effect=[product, image]),
            patch.object(management_views, "ProductImageMetadataForm", return_value=valid_form),
            patch.object(management_views, "update_image_metadata"),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="valid") as redirect_mock,
        ):
            response = unwrap(management_views.product_image_update)(request, "product-id", "image-id")
        self.assertEqual(response, "valid")
        redirect_mock.assert_called_once_with(
            management_views.MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id
        )

    def test_product_image_primary_and_delete_redirects(self):
        request = self.request()
        product = SimpleNamespace(public_id="product-id")
        image = SimpleNamespace(public_id="image-id")
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", side_effect=[product, image]),
            patch.object(management_views, "set_primary_image"),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="primary") as redirect_mock,
        ):
            response = unwrap(management_views.product_image_primary)(request, "product-id", "image-id")
        self.assertEqual(response, "primary")
        redirect_mock.assert_called_once_with(
            management_views.MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id
        )

        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", side_effect=[product, image]),
            patch.object(management_views, "delete_product_image"),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="deleted") as redirect_mock,
        ):
            response = unwrap(management_views.product_image_delete)(request, "product-id", "image-id")
        self.assertEqual(response, "deleted")
        redirect_mock.assert_called_once_with(
            management_views.MANAGEMENT_PRODUCT_IMAGES_URL, public_id=product.public_id
        )

    def test_pricing_success_and_get_render_paths(self):
        request = self.request()
        product = SimpleNamespace(
            product_reference="REF-1",
            sku="HS00001",
            cost_price=10,
            selling_price=20,
            discount_price=15,
        )
        updated = SimpleNamespace(cost_price=11, selling_price=21, discount_price=16)
        form = MagicMock()
        form.is_valid.return_value = True
        form.save.return_value = updated
        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "get_object_or_404", return_value=product),
            patch.object(management_views, "PricingForm", return_value=form),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.pricing)(request, "product-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_PRODUCTS_URL)

        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "get_object_or_404", return_value=product),
            patch.object(management_views, "PricingForm", return_value=MagicMock()),
            patch.object(management_views, "render", return_value="rendered") as render_mock,
        ):
            response = unwrap(management_views.pricing)(self.request(method="GET"), "product-id")
        self.assertEqual(response, "rendered")
        self.assertEqual(render_mock.call_args.args[1], management_views.MANAGEMENT_FORM_TEMPLATE)

    def test_inventory_adjust_success_and_get_render_paths(self):
        request = self.request()
        product = SimpleNamespace(pk=1, sku="HS00001")
        locked = SimpleNamespace(
            available_quantity=5,
            reserved_quantity=1,
            save=MagicMock(),
        )
        form = MagicMock()
        form.is_valid.return_value = True
        form.cleaned_data = {"delta": 2, "reason": "Stock count"}
        manager = MagicMock()
        manager.select_for_update.return_value.get.return_value = locked
        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=product),
            patch.object(management_views, "InventoryAdjustmentForm", return_value=form),
            patch.object(management_views.Product, "objects", manager),
            patch.object(management_views.InventoryTransaction.objects, "create"),
            patch.object(management_views.transaction, "atomic", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: False)),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.inventory_adjust)(request, "product-id")
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_PRODUCTS_URL)

        with (
            patch.object(management_views, "require_permission"),
            patch.object(management_views, "get_object_or_404", return_value=product),
            patch.object(management_views, "InventoryAdjustmentForm", return_value=MagicMock()),
            patch.object(management_views, "render", return_value="rendered") as render_mock,
        ):
            response = unwrap(management_views.inventory_adjust)(self.request(method="GET"), "product-id")
        self.assertEqual(response, "rendered")
        self.assertEqual(render_mock.call_args.args[1], management_views.MANAGEMENT_FORM_TEMPLATE)

    def test_promotion_create_edit_and_toggle_redirects(self):
        request = self.request()
        promotion = SimpleNamespace(
            name_ar="عرض",
            scope="ALL",
            discount_type="PERCENT",
            discount_value=10,
            is_active=True,
            full_clean=MagicMock(),
            save=MagicMock(),
        )
        form = MagicMock()
        form.is_valid.return_value = True
        form.save.return_value = promotion
        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "PromotionManagementForm", return_value=form),
            patch.object(management_views.transaction, "atomic", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: False)),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="created") as redirect_mock,
        ):
            response = unwrap(management_views.promotion_create)(request)
        self.assertEqual(response, "created")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_PROMOTIONS_URL)

        existing = SimpleNamespace(name_ar="قديم", is_active=True, discount_value=5)
        updated = SimpleNamespace(
            name_ar="جديد",
            is_active=False,
            discount_value=7,
            full_clean=MagicMock(),
            save=MagicMock(),
        )
        edit_form = MagicMock()
        edit_form.is_valid.return_value = True
        edit_form.save.return_value = updated
        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "get_object_or_404", return_value=existing),
            patch.object(management_views, "PromotionManagementForm", return_value=edit_form),
            patch.object(management_views.transaction, "atomic", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: False)),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="edited") as redirect_mock,
        ):
            response = unwrap(management_views.promotion_edit)(request, "promotion-id")
        self.assertEqual(response, "edited")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_PROMOTIONS_URL)

        toggle = SimpleNamespace(is_active=True, save=MagicMock())
        with (
            patch.object(management_views, "require_owner"),
            patch.object(management_views, "get_object_or_404", return_value=toggle),
            patch.object(management_views, "audit"),
            patch.object(management_views, "redirect", return_value="toggled") as redirect_mock,
        ):
            response = unwrap(management_views.promotion_toggle)(request, "promotion-id")
        self.assertEqual(response, "toggled")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_PROMOTIONS_URL)

    def test_reservation_override_already_processed_redirect(self):
        request = self.request(post={"request_id": "1", "request_action": "approve"})
        processed = SimpleNamespace(status="APPROVED")
        queryset = MagicMock()
        queryset.select_for_update.return_value.select_related.return_value = queryset
        with (
            patch("accounts.services.permission_service.require_owner"),
            patch.object(management_views.transaction, "atomic", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: False)),
            patch.object(management_views.ReservationLimitRequest, "objects", queryset),
            patch.object(management_views, "get_object_or_404", return_value=processed),
            patch.object(management_views.messages, "info"),
            patch.object(management_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(management_views.reservation_overrides)(request)
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(management_views.MANAGEMENT_RESERVATION_OVERRIDES_URL)


class OrdersNewCodeCoverageTests(RequestFactoryMixin, SimpleTestCase):
    def test_reservation_limit_low_and_high_redirects(self):
        user = SimpleNamespace(role="CUSTOMER", is_authenticated=True)
        for quantity in (1, 999):
            request = self.request(user=user)
            cart = SimpleNamespace()
            cart.items = MagicMock()
            cart.items.values_list.return_value = [quantity]
            with (
                patch.object(order_views, "get_cart", return_value=cart),
                patch.object(order_views, "sanitize_cart"),
                patch.object(order_views.messages, "info"),
                patch.object(order_views.messages, "error"),
                patch.object(order_views, "redirect", return_value="redirected") as redirect_mock,
            ):
                response = unwrap(order_views.reservation_limit_request)(request)
            self.assertEqual(response, "redirected")
            redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

    def test_cart_remove_redirect(self):
        request = self.request()
        item = SimpleNamespace(id=3)
        cart = SimpleNamespace(items=MagicMock())
        cart.items.select_related.return_value = cart.items
        with (
            patch.object(order_views, "get_cart", return_value=cart),
            patch.object(order_views, "sanitize_cart"),
            patch.object(order_views, "get_object_or_404", return_value=item),
            patch.object(order_views, "remove", return_value={"quantity": 1}),
            patch.object(order_views, "audit"),
            patch.object(order_views, "_is_ajax", return_value=False),
            patch.object(order_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(order_views.cart_remove)(request, 3)
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

    def test_cart_quantity_invalid_and_success_redirects(self):
        request = self.request(post={"quantity": "2"})
        cart = SimpleNamespace()
        with (
            patch.object(order_views, "get_cart", return_value=cart),
            patch.object(order_views, "sanitize_cart"),
            patch.object(order_views, "set_quantity", side_effect=ValueError("invalid")),
            patch.object(order_views, "_is_ajax", return_value=False),
            patch.object(order_views.messages, "error"),
            patch.object(order_views, "redirect", return_value="invalid") as redirect_mock,
        ):
            response = unwrap(order_views.cart_quantity)(request, 3)
        self.assertEqual(response, "invalid")
        redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

        item = SimpleNamespace(product=SimpleNamespace(product_reference="REF"), quantity=2)
        with (
            patch.object(order_views, "get_cart", return_value=cart),
            patch.object(order_views, "sanitize_cart"),
            patch.object(order_views, "set_quantity", return_value=item),
            patch.object(order_views, "audit"),
            patch.object(order_views, "_is_ajax", return_value=False),
            patch.object(order_views, "redirect", return_value="success") as redirect_mock,
        ):
            response = unwrap(order_views.cart_quantity)(request, 3)
        self.assertEqual(response, "success")
        redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

    def test_empty_follow_up_and_checkout_redirects(self):
        request = self.request()
        cart = SimpleNamespace(items=MagicMock())
        cart.items.exists.return_value = False
        with (
            patch.object(order_views, "get_cart", return_value=cart),
            patch.object(order_views, "redirect", return_value="follow-up") as redirect_mock,
        ):
            response = unwrap(order_views.cart_follow_up)(request)
        self.assertEqual(response, "follow-up")
        redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

        with (
            patch.object(order_views, "get_cart", return_value=cart),
            patch.object(order_views, "sanitize_cart", return_value=[]),
            patch.object(order_views, "redirect", return_value="checkout") as redirect_mock,
        ):
            response = unwrap(order_views.checkout)(request)
        self.assertEqual(response, "checkout")
        redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

    def test_checkout_conflict_redirect(self):
        request = self.request()
        cart = SimpleNamespace(items=MagicMock())
        cart.items.exists.return_value = True
        with (
            patch.object(order_views, "get_cart", return_value=cart),
            patch.object(order_views, "sanitize_cart", return_value=[]),
            patch.object(order_views, "_checkout_conflicts", return_value=[{"sku": "HS1", "kind": "reserved"}]),
            patch.object(order_views.messages, "warning"),
            patch.object(order_views, "redirect", return_value="redirected") as redirect_mock,
        ):
            response = unwrap(order_views.checkout)(request)
        self.assertEqual(response, "redirected")
        redirect_mock.assert_called_once_with(order_views.ORDERS_CART_URL)

    def test_stripe_start_value_error_and_provider_error_redirects(self):
        request = self.request()
        order = SimpleNamespace(
            public_id="order-id",
            status="PENDING",
            payment_status="UNPAID",
            refresh_from_db=MagicMock(),
        )
        policy = SimpleNamespace(online=True)
        with (
            patch.object(order_views, "get_object_or_404", return_value=order),
            patch.object(order_views, "_can_access_order", return_value=True),
            patch.object(order_views, "expire_unpaid_order_if_needed"),
            patch.object(order_views, "current_payment_policy", return_value=policy),
            patch.object(order_views.messages, "error"),
            patch.object(
                order_views, "create_checkout_session", side_effect=ValueError("no")
            ),
            patch.object(
                order_views, "redirect", return_value="value"
            ) as redirect_mock,
        ):
            response = unwrap(order_views.stripe_payment_start)(request, "order-id")
        self.assertEqual(response, "value")
        redirect_mock.assert_called_once_with(
            order_views.ORDERS_CONFIRMATION_URL, public_id="order-id"
        )

        with (
            patch.object(order_views, "get_object_or_404", return_value=order),
            patch.object(order_views, "_can_access_order", return_value=True),
            patch.object(order_views, "expire_unpaid_order_if_needed"),
            patch.object(order_views, "current_payment_policy", return_value=policy),
            patch.object(order_views.messages, "error"),
            patch.object(
                order_views,
                "create_checkout_session",
                side_effect=RuntimeError("provider"),
            ),
            patch.object(
                order_views, "redirect", return_value="provider"
            ) as redirect_mock,
        ):
            response = unwrap(order_views.stripe_payment_start)(request, "order-id")
        self.assertEqual(response, "provider")
        redirect_mock.assert_called_once_with(
            order_views.ORDERS_CONFIRMATION_URL, public_id="order-id"
        )

    def test_manual_payment_paid_and_no_destination_redirects(self):
        request = self.request()
        paid = SimpleNamespace(
            public_id="paid-id",
            status="PENDING",
            payment_status=order_views.Order.PaymentStatus.PAID,
            refresh_from_db=MagicMock(),
        )
        policy = SimpleNamespace(manual=True)
        with (
            patch.object(order_views, "get_object_or_404", return_value=paid),
            patch.object(order_views, "_can_access_order", return_value=True),
            patch.object(order_views, "expire_unpaid_order_if_needed"),
            patch.object(order_views, "current_payment_policy", return_value=policy),
            patch.object(order_views, "redirect", return_value="paid") as redirect_mock,
        ):
            response = unwrap(order_views.manual_payment_start)(request, "paid-id")
        self.assertEqual(response, "paid")
        redirect_mock.assert_called_once_with(order_views.ORDERS_DETAIL_URL, public_id="paid-id")

        unpaid = SimpleNamespace(
            public_id="unpaid-id",
            status="PENDING",
            payment_status="UNPAID",
            refresh_from_db=MagicMock(),
        )
        with (
            patch.object(order_views, "get_object_or_404", return_value=unpaid),
            patch.object(order_views, "_can_access_order", return_value=True),
            patch.object(order_views, "expire_unpaid_order_if_needed"),
            patch.object(order_views, "current_payment_policy", return_value=policy),
            patch.object(order_views, "whatsapp_url", return_value=""),
            patch.object(order_views.messages, "error"),
            patch.object(order_views, "redirect", return_value="missing") as redirect_mock,
        ):
            response = unwrap(order_views.manual_payment_start)(request, "unpaid-id")
        self.assertEqual(response, "missing")
        redirect_mock.assert_called_once_with(order_views.ORDERS_DETAIL_URL, public_id="unpaid-id")


class AdditionalNewCodeCoverageTests(RequestFactoryMixin, SimpleTestCase):
    def test_account_register_authenticated_redirect(self):
        request = self.request(user=SimpleNamespace(is_authenticated=True))
        with patch.object(account_views, "redirect", return_value="home") as redirect_mock:
            response = account_views.register(request)
        self.assertEqual(response, "home")
        redirect_mock.assert_called_once_with(account_views.CORE_HOME_URL)

    def test_login_authenticated_owner_and_customer_redirects(self):
        owner = SimpleNamespace(is_authenticated=True, role=account_views.User.Role.OWNER)
        with patch.object(account_views, "redirect", return_value="management") as redirect_mock:
            response = account_views.login_view(self.request(user=owner))
        self.assertEqual(response, "management")
        redirect_mock.assert_called_once_with(account_views.MANAGEMENT_DASHBOARD_URL)

        customer = SimpleNamespace(is_authenticated=True, role=account_views.User.Role.CUSTOMER)
        with patch.object(account_views, "redirect", return_value="home") as redirect_mock:
            response = account_views.login_view(self.request(user=customer))
        self.assertEqual(response, "home")
        redirect_mock.assert_called_once_with(account_views.CORE_HOME_URL)


    def test_logout_and_mfa_guard_redirects(self):
        user = SimpleNamespace(
            is_authenticated=True,
            role=account_views.User.Role.OWNER,
        )
        request = self.request(user=user)
        with (
            patch.object(account_views, "record_event"),
            patch.object(account_views, "logout"),
            patch.object(account_views, "redirect", return_value="home") as redirect_mock,
        ):
            response = unwrap(account_views.logout_view)(request)
        self.assertEqual(response, "home")
        redirect_mock.assert_called_once_with(account_views.CORE_HOME_URL)

        with (
            patch.object(account_views, "get_preauth_user", return_value=None),
            patch.object(account_views, "clear_preauth"),
            patch.object(account_views, "redirect", return_value="login") as redirect_mock,
        ):
            response = unwrap(account_views.mfa_verify)(self.request(method="GET"))
        self.assertEqual(response, "login")
        redirect_mock.assert_called_once_with(account_views.ACCOUNTS_LOGIN_URL)

        manager = MagicMock()
        manager.filter.return_value.delete.return_value = (0, {})
        with (
            patch.object(account_views.MFADevice, "objects", manager),
            patch.object(account_views, "record_event"),
            patch.object(account_views, "logout"),
            patch.object(account_views, "redirect", return_value="cancelled") as redirect_mock,
        ):
            response = unwrap(account_views.mfa_cancel_setup)(request)
        self.assertEqual(response, "cancelled")
        redirect_mock.assert_called_once_with(account_views.ACCOUNTS_LOGIN_URL)

    def test_ambassador_gift_disabled_low_balance_and_existing_request_redirects(self):
        user = SimpleNamespace(role=ambassador_views.User.Role.CUSTOMER, is_authenticated=True)
        request = self.request(user=user)
        cfg = SimpleNamespace(enabled=False, redeem_points_block=1000)
        with (
            patch.object(ambassador_views, "settings_obj", return_value=cfg),
            patch.object(ambassador_views.messages, "error"),
            patch.object(ambassador_views, "redirect", return_value="disabled") as redirect_mock,
        ):
            response = unwrap(ambassador_views.request_gift)(request)
        self.assertEqual(response, "disabled")
        redirect_mock.assert_called_once_with(ambassador_views.AMBASSADOR_ACCOUNT_URL)

        cfg.enabled = True
        profile = SimpleNamespace(redemptions=MagicMock())
        with (
            patch.object(ambassador_views, "settings_obj", return_value=cfg),
            patch.object(ambassador_views, "ensure_profile", return_value=profile),
            patch.object(ambassador_views, "available_points", return_value=10),
            patch.object(ambassador_views.messages, "error"),
            patch.object(ambassador_views, "redirect", return_value="low") as redirect_mock,
        ):
            response = unwrap(ambassador_views.request_gift)(request)
        self.assertEqual(response, "low")
        redirect_mock.assert_called_once_with(ambassador_views.AMBASSADOR_ACCOUNT_URL)

        profile.redemptions.filter.return_value.exists.return_value = True
        with (
            patch.object(ambassador_views, "settings_obj", return_value=cfg),
            patch.object(ambassador_views, "ensure_profile", return_value=profile),
            patch.object(ambassador_views, "available_points", return_value=2000),
            patch.object(ambassador_views.messages, "info"),
            patch.object(ambassador_views, "redirect", return_value="existing") as redirect_mock,
        ):
            response = unwrap(ambassador_views.request_gift)(request)
        self.assertEqual(response, "existing")
        redirect_mock.assert_called_once_with(ambassador_views.AMBASSADOR_ACCOUNT_URL)
