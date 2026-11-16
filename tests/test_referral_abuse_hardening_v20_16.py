from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from ambassadors.models import (
    AmbassadorProfile,
    AmbassadorProgramSetting,
    PointBatch,
    PointLedger,
    Referral,
)
from ambassadors.services.program import create_pending_referral, reconcile_referral
from orders.models import Order


class ReferralAbuseHardeningV2016Tests(TestCase):
    def setUp(self):
        cfg = AmbassadorProgramSetting.load()
        cfg.enabled = True
        cfg.save(update_fields=["enabled"])
        self.amb = User.objects.create_user(
            username="amb16",
            email="amb16@example.com",
            phone_e164="+971501111116",
            password="StrongPass!12345",
            role=User.Role.CUSTOMER,
        )
        self.buyer = User.objects.create_user(
            username="buyer16",
            email="buyer16@example.com",
            phone_e164="+971502222226",
            password="StrongPass!12345",
            role=User.Role.CUSTOMER,
        )
        self.profile = AmbassadorProfile.objects.get(user=self.amb)

    def order(self, *, user=None, phone="+971509999999", email="other@example.com"):
        return Order.objects.create(
            reference=f"HS-RA-{Order.objects.count() + 1:05d}",
            user=user,
            customer_name="Buyer",
            customer_email=email,
            customer_phone=phone,
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("2000.00"),
            discount_total=0,
            tax_total=0,
            shipping_total=0,
            grand_total=Decimal("2000.00"),
        )

    def deliver_paid(self, order):
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.DELIVERED
        order.save(update_fields=["payment_status", "status"])

    def test_guest_with_different_phone_and_email_never_auto_awards(self):
        order = self.order(user=None)
        ref = create_pending_referral(order=order, code=self.profile.code, buyer=None)
        self.deliver_paid(order)
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.MANUAL_REVIEW)
        self.assertEqual(ref.review_reason, "GUEST_IDENTITY_UNVERIFIED")
        self.assertEqual(ref.points_awarded, 0)
        self.assertFalse(PointBatch.objects.filter(referral=ref).exists())
        self.assertFalse(
            PointLedger.objects.filter(
                referral=ref, kind=PointLedger.Kind.EARN
            ).exists()
        )

    def test_reconciliation_is_idempotent_while_under_review(self):
        order = self.order(user=None)
        ref = create_pending_referral(order=order, code=self.profile.code, buyer=None)
        self.deliver_paid(order)
        reconcile_referral(order)
        reconcile_referral(order)
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.MANUAL_REVIEW)
        self.assertEqual(PointBatch.objects.filter(referral=ref).count(), 0)

    def test_authenticated_independent_buyer_still_awards(self):
        order = self.order(
            user=self.buyer, phone=self.buyer.phone_e164, email=self.buyer.email
        )
        ref = create_pending_referral(
            order=order, code=self.profile.code, buyer=self.buyer
        )
        self.deliver_paid(order)
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.AWARDED)
        self.assertEqual(PointBatch.objects.filter(referral=ref).count(), 1)

    def test_owner_approval_path_can_award_reviewed_guest_once(self):
        order = self.order(user=None)
        ref = create_pending_referral(order=order, code=self.profile.code, buyer=None)
        self.deliver_paid(order)
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.MANUAL_REVIEW)
        ref.status = Referral.Status.PENDING
        ref.review_reason = "OWNER_APPROVED"
        ref.save(update_fields=["status", "review_reason"])
        reconcile_referral(order, owner_approved=True)
        reconcile_referral(order, owner_approved=True)
        ref.refresh_from_db()
        self.assertEqual(ref.status, Referral.Status.AWARDED)
        self.assertEqual(PointBatch.objects.filter(referral=ref).count(), 1)
        self.assertEqual(
            PointLedger.objects.filter(
                referral=ref, kind=PointLedger.Kind.EARN
            ).count(),
            1,
        )

    def test_authenticated_self_referral_still_rejected_at_creation(self):
        order = self.order(
            user=self.amb, phone="+971508888888", email="alias@example.com"
        )
        with self.assertRaises(ValueError):
            create_pending_referral(order=order, code=self.profile.code, buyer=self.amb)
