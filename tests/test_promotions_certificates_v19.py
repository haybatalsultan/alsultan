from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, User
from catalog.models import Category, Product, Promotion
from catalog.services.promotion_service import price_snapshot
from core.forms import PromotionManagementForm
from tests.helpers import login_management


class PromotionPricingSecurityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-v19"
        )
        self.product = Product.objects.create(
            name_ar="مسبحة عرض",
            name_en="Promotion Misbah",
            category=self.category,
            cost_price=Decimal("40.00"),
            selling_price=Decimal("100.00"),
            available_quantity=2,
            status=Product.Status.AVAILABLE,
        )

    def test_active_product_promotion_applies_single_server_price_and_gift(self):
        promo = Promotion.objects.create(
            name_ar="عرض 20%",
            name_en="20 Percent",
            scope=Promotion.Scope.PRODUCTS,
            discount_type=Promotion.DiscountType.PERCENT,
            discount_value=Decimal("20.00"),
            gift_name_ar="كركوشة فاخرة",
            gift_name_en="Premium Tassel",
            gift_quantity=1,
            starts_at=timezone.now() - timezone.timedelta(minutes=5),
            ends_at=timezone.now() + timezone.timedelta(days=1),
            is_active=True,
        )
        promo.products.add(self.product)
        snap = price_snapshot(self.product)
        self.assertEqual(snap["base_price"], Decimal("100.00"))
        self.assertEqual(snap["final_price"], Decimal("80.00"))
        self.assertEqual(snap["discount_amount"], Decimal("20.00"))
        self.assertEqual(snap["gift_ar"], "كركوشة فاخرة")

    def test_expired_or_inactive_promotions_never_apply(self):
        promo = Promotion.objects.create(
            name_ar="منتهي",
            name_en="Expired",
            scope=Promotion.Scope.ALL,
            discount_type=Promotion.DiscountType.PERCENT,
            discount_value=Decimal("50.00"),
            starts_at=timezone.now() - timezone.timedelta(days=2),
            ends_at=timezone.now() - timezone.timedelta(days=1),
            is_active=True,
        )
        snap = price_snapshot(self.product)
        self.assertEqual(snap["final_price"], Decimal("100.00"))

    def test_product_discount_and_promotion_do_not_stack(self):
        self.product.discount_price = Decimal("70.00")
        self.product.save(update_fields=["discount_price", "updated_at"])
        promo = Promotion.objects.create(
            name_ar="عرض",
            name_en="Promotion",
            scope=Promotion.Scope.ALL,
            discount_type=Promotion.DiscountType.PERCENT,
            discount_value=Decimal("20.00"),
            gift_name_ar="هدية",
            starts_at=timezone.now() - timezone.timedelta(minutes=1),
            ends_at=timezone.now() + timezone.timedelta(days=1),
            is_active=True,
        )
        snap = price_snapshot(self.product)
        self.assertEqual(snap["final_price"], Decimal("70.00"))
        self.assertEqual(snap["source"], "PRODUCT")
        self.assertFalse(snap["has_gift"])

    def test_fixed_discount_cannot_equal_or_exceed_cheapest_target_price(self):
        data = {
            "name_ar": "خصم خاطئ",
            "name_en": "Unsafe Discount",
            "scope": Promotion.Scope.PRODUCTS,
            "products": [self.product.pk],
            "discount_type": Promotion.DiscountType.FIXED,
            "discount_value": "100.00",
            "gift_quantity": "1",
            "starts_at": (timezone.now() + timezone.timedelta(minutes=1)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "ends_at": (timezone.now() + timezone.timedelta(days=1)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "priority": "100",
        }
        form = PromotionManagementForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("discount_value", form.errors)


class PromotionOwnerAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "promo-owner", password="VeryStrongPass!123", role=User.Role.OWNER
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )
        self.supervisor = User.objects.create_user(
            "promo-sup", password="VeryStrongPass!123", role=User.Role.SUPERVISOR
        )

    def _owner_login(self):
        self.client.login(username="promo-owner", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    def test_owner_can_open_promotions_page(self):
        self._owner_login()
        self.assertEqual(
            self.client.get(reverse("core:management_promotions")).status_code, 200
        )

    def test_supervisor_cannot_open_promotions_page(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_promotions")).status_code, 403
        )

    def test_toggle_rejects_get(self):
        self._owner_login()
        promo = Promotion.objects.create(
            name_ar="عرض",
            name_en="Offer",
            scope=Promotion.Scope.ALL,
            discount_type=Promotion.DiscountType.PERCENT,
            discount_value=Decimal("10.00"),
            starts_at=timezone.now(),
            ends_at=timezone.now() + timezone.timedelta(days=1),
        )
        self.assertEqual(
            self.client.get(
                reverse("core:management_promotion_toggle", args=[promo.public_id])
            ).status_code,
            405,
        )


class ProductVerificationStorefrontTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-verification-v19"
        )

    def _product(self, **extra):
        data = dict(
            name_ar="مسبحة",
            name_en="Misbah",
            category=self.category,
            cost_price=Decimal("40.00"),
            selling_price=Decimal("100.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        data.update(extra)
        return Product.objects.create(**data)

    def test_default_product_without_verification_is_valid_and_has_no_badge(self):
        product = self._product()
        self.assertEqual(product.verification_status, Product.VerificationStatus.NONE)
        response = self.client.get(reverse("catalog:detail", args=[product.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "تم فحص المنتج")
        self.assertNotContains(response, "موثق بشهادة")

    def test_inspected_product_badge_is_visible(self):
        product = self._product(
            verification_status=Product.VerificationStatus.INSPECTED
        )
        response = self.client.get(reverse("catalog:detail", args=[product.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تم فحص المنتج")
        self.assertNotContains(response, "موثق بشهادة")

    def test_certified_product_badge_is_visible(self):
        product = self._product(
            verification_status=Product.VerificationStatus.CERTIFIED
        )
        response = self.client.get(reverse("catalog:detail", args=[product.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "موثق بشهادة")

    def test_supervisor_product_form_cannot_change_verification_claim(self):
        from accounts.models import SupervisorPermission

        supervisor = User.objects.create_user(
            "verify-sup", password="VeryStrongPass!123", role=User.Role.SUPERVISOR
        )
        SupervisorPermission.objects.create(
            user=supervisor, view_products=True, edit_products=True
        )
        product = self._product(verification_status=Product.VerificationStatus.NONE)
        login_management(self.client, supervisor, "VeryStrongPass!123")
        response = self.client.post(
            reverse("core:management_product_edit", args=[product.public_id]),
            {
                "name_ar": product.name_ar,
                "name_en": product.name_en,
                "category": str(self.category.pk),
                "available_quantity": "1",
                "status": Product.Status.AVAILABLE,
                # Forged field: supervisor forms must ignore it server-side.
                "verification_status": Product.VerificationStatus.CERTIFIED,
            },
        )
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.verification_status, Product.VerificationStatus.NONE)

    def test_database_rejects_unknown_verification_status(self):
        from django.db import IntegrityError, transaction

        product = self._product()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.filter(pk=product.pk).update(verification_status="FORGED")


class PromotionOrderSnapshotTests(TestCase):
    def test_checkout_recalculates_promotion_server_side_and_snapshots_gift(self):
        from orders.models import Cart, CartItem
        from orders.services.order_service import create_order_from_cart

        user = User.objects.create_user(
            "promo-customer", password="VeryStrongPass!123", role=User.Role.CUSTOMER
        )
        category = Category.objects.create(
            name_ar="كهرمان", name_en="Amber", slug="promo-order-amber"
        )
        product = Product.objects.create(
            name_ar="قطعة",
            name_en="Piece",
            category=category,
            cost_price=Decimal("20.00"),
            selling_price=Decimal("100.00"),
            available_quantity=1,
            status=Product.Status.AVAILABLE,
        )
        promo = Promotion.objects.create(
            name_ar="خصم آمن",
            name_en="Secure Promotion",
            scope=Promotion.Scope.ALL,
            discount_type=Promotion.DiscountType.PERCENT,
            discount_value=Decimal("25.00"),
            gift_name_ar="كركوشة",
            starts_at=timezone.now() - timezone.timedelta(minutes=1),
            ends_at=timezone.now() + timezone.timedelta(days=1),
            is_active=True,
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        customer = {
            "customer_name": "Test",
            "customer_email": "",
            "customer_phone": "+971501234567",
            "country": "AE",
            "emirate": "Abu Dhabi",
            "city": "",
            "area": "Khalifa City",
            "street": "",
            "building": "",
            "apartment_or_villa": "",
            "postal_code": "",
            "additional_notes": "",
            "latitude": None,
            "longitude": None,
            "policy_acceptance": True,
        }
        order = create_order_from_cart(
            cart=cart, customer=customer, user=user, idempotency_key="promo-order-1"
        )
        item = order.items.get()
        self.assertEqual(item.base_unit_price, Decimal("100.00"))
        self.assertEqual(item.unit_price, Decimal("75.00"))
        self.assertEqual(item.discount, Decimal("25.00"))
        self.assertEqual(item.promotion_label, "خصم آمن")
        self.assertEqual(item.gift_label, "كركوشة")
        self.assertEqual(order.subtotal, Decimal("100.00"))
        self.assertEqual(order.discount_total, Decimal("25.00"))
        self.assertEqual(order.grand_total, Decimal("75.00"))
