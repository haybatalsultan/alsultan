from datetime import timedelta
from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from ambassadors.models import (
    AmbassadorProfile,
    AmbassadorProgramSetting,
    PointBatch,
    Referral,
)
from ambassadors.services.program import (
    available_points,
    create_pending_referral,
    discount_for_points,
    points_for_amount,
)
from orders.models import Order


class AmbassadorRulesTests(TestCase):
    def setUp(self):
        self.cfg = AmbassadorProgramSetting.load()
        self.cfg.enabled = True
        self.cfg.save(update_fields=["enabled"])
        self.ambassador_user = User.objects.create_user(
            username="amb",
            email="amb@example.com",
            phone_e164="+971501111111",
            password="VeryStrongPass123!",
            role=User.Role.CUSTOMER,
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            phone_e164="+971502222222",
            password="VeryStrongPass123!",
            role=User.Role.CUSTOMER,
        )
        self.profile = AmbassadorProfile.objects.get(user=self.ambassador_user)

    def order(self, amount=Decimal("1000.00"), user=None):
        return Order.objects.create(
            reference=f"HS-T-{Order.objects.count() + 1:06d}",
            user=user,
            customer_name="Buyer",
            customer_email="buyer@example.com",
            customer_phone="+971502222222",
            country="AE",
            area="Abu Dhabi",
            subtotal=amount,
            discount_total=0,
            tax_total=0,
            shipping_total=0,
            grand_total=amount,
        )

    def test_earning_uses_complete_1000_aed_blocks_only(self):
        self.assertEqual(points_for_amount(Decimal("999.99"), self.cfg), 0)
        self.assertEqual(points_for_amount(Decimal("1000.00"), self.cfg), 25)
        self.assertEqual(points_for_amount(Decimal("1999.99"), self.cfg), 25)
        self.assertEqual(points_for_amount(Decimal("2000.00"), self.cfg), 50)

    def test_redemption_rule_is_1000_points_equals_25_aed(self):
        self.assertEqual(discount_for_points(999, self.cfg), Decimal("0.00"))
        self.assertEqual(discount_for_points(1000, self.cfg), Decimal("25.00"))
        self.assertEqual(discount_for_points(2000, self.cfg), Decimal("50.00"))

    def test_authenticated_self_referral_is_rejected(self):
        order = self.order(user=self.ambassador_user)
        with self.assertRaises(ValueError):
            create_pending_referral(
                order=order, code=self.profile.code, buyer=self.ambassador_user
            )

    def test_guest_self_referral_by_phone_or_email_is_rejected(self):
        order = self.order(user=None)
        order.customer_phone = self.ambassador_user.phone_e164
        order.customer_email = ""
        order.save(update_fields=["customer_phone", "customer_email"])
        with self.assertRaises(ValueError):
            create_pending_referral(order=order, code=self.profile.code, buyer=None)

    def test_points_award_only_when_paid_and_delivered(self):
        order = self.order(Decimal("4500.00"), user=self.buyer)
        ref = create_pending_referral(
            order=order, code=self.profile.code, buyer=self.buyer
        )
        self.assertEqual(ref.status, Referral.Status.PENDING)
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["payment_status"])
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.PENDING)
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["status"])
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.AWARDED)
        self.assertEqual(ref.points_awarded, 100)

    def test_each_batch_has_its_own_12_month_expiry(self):
        order = self.order(Decimal("1000.00"), user=self.buyer)
        ref = create_pending_referral(
            order=order, code=self.profile.code, buyer=self.buyer
        )
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["payment_status", "status"])
        batch = PointBatch.objects.get(referral=ref)
        self.assertGreater(batch.expires_at, batch.earned_at + timedelta(days=364))
        self.assertLess(batch.expires_at, batch.earned_at + timedelta(days=367))

    def test_full_refund_reverses_unspent_referral_points(self):
        order = self.order(Decimal("2000.00"), user=self.buyer)
        ref = create_pending_referral(
            order=order, code=self.profile.code, buyer=self.buyer
        )
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["payment_status", "status"])
        self.assertEqual(available_points(self.profile), 50)
        order.payment_status = Order.PaymentStatus.REFUNDED
        order.save(update_fields=["payment_status"])
        self.assertEqual(available_points(self.profile), 0)
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.CANCELLED)

    def test_program_disabled_rejects_new_referral(self):
        self.cfg.enabled = False
        self.cfg.save(update_fields=["enabled"])
        order = self.order(user=self.buyer)
        self.assertIsNone(
            create_pending_referral(
                order=order, code=self.profile.code, buyer=self.buyer
            )
        )
