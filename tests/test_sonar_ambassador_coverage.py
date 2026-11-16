from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ambassadors.models import (
    AmbassadorProfile,
    PointLedger,
    Referral,
)
from orders.models import Order
from tests.helpers import login_management


class AmbassadorManagementCoverageTests(TestCase):
    OWNER_PASSWORD = "StrongPass!12345"

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner-sonar-amb",
            email="owner-sonar-amb@example.com",
            password=self.OWNER_PASSWORD,
            role=User.Role.OWNER,
        )
        login_management(self.client, self.owner, self.OWNER_PASSWORD)

        self.ambassador_user = User.objects.create_user(
            username="amb-sonar",
            email="amb-sonar@example.com",
            phone_e164="+971501234501",
            password="CustomerPass!12345",
            role=User.Role.CUSTOMER,
        )
        self.profile = AmbassadorProfile.objects.get(user=self.ambassador_user)

    def _order(self, suffix, *, status=Order.Status.PENDING, payment_status=Order.PaymentStatus.UNPAID):
        return Order.objects.create(
            reference=f"HS-SONAR-{suffix}",
            customer_name="Coverage Buyer",
            customer_email="coverage@example.com",
            customer_phone="+971501234599",
            country="AE",
            area="Abu Dhabi",
            subtotal=Decimal("1000.00"),
            discount_total=Decimal("0.00"),
            tax_total=Decimal("0.00"),
            shipping_total=Decimal("0.00"),
            grand_total=Decimal("1000.00"),
            status=status,
            payment_status=payment_status,
        )

    def _referral(self, suffix, *, status=Referral.Status.MANUAL_REVIEW, order_status=Order.Status.PENDING, payment_status=Order.PaymentStatus.UNPAID):
        order = self._order(
            suffix,
            status=order_status,
            payment_status=payment_status,
        )
        referral = Referral.objects.create(
            order=order,
            ambassador=self.profile,
            code_snapshot=self.profile.code,
            eligible_amount=Decimal("1000.00"),
            status=status,
        )
        return referral

    def test_toggle_program_redirects_back_to_dashboard(self):
        response = self.client.post(reverse("core:management_ambassadors_toggle"))
        self.assertRedirects(
            response,
            reverse("core:management_ambassadors"),
            fetch_redirect_response=False,
        )

    def test_review_non_review_referral_redirects(self):
        referral = self._referral("NONREVIEW", status=Referral.Status.PENDING)
        response = self.client.post(
            reverse("core:management_ambassador_referral_review", args=[referral.pk]),
            {"decision": "approve"},
        )
        self.assertRedirects(
            response,
            reverse("core:management_ambassadors"),
            fetch_redirect_response=False,
        )

    def test_review_reject_redirects_and_marks_rejected(self):
        referral = self._referral("REJECT")
        response = self.client.post(
            reverse("core:management_ambassador_referral_review", args=[referral.pk]),
            {"decision": "reject"},
        )
        self.assertRedirects(
            response,
            reverse("core:management_ambassadors"),
            fetch_redirect_response=False,
        )
        referral.refresh_from_db()
        self.assertEqual(referral.status, Referral.Status.REJECTED)
        self.assertEqual(referral.review_reason, "OWNER_REJECTED")

    def test_review_invalid_decision_redirects(self):
        referral = self._referral("INVALID")
        response = self.client.post(
            reverse("core:management_ambassador_referral_review", args=[referral.pk]),
            {"decision": "later"},
        )
        self.assertRedirects(
            response,
            reverse("core:management_ambassadors"),
            fetch_redirect_response=False,
        )

    def test_review_incomplete_order_redirects(self):
        referral = self._referral("INCOMPLETE")
        response = self.client.post(
            reverse("core:management_ambassador_referral_review", args=[referral.pk]),
            {"decision": "approve"},
        )
        self.assertRedirects(
            response,
            reverse("core:management_ambassadors"),
            fetch_redirect_response=False,
        )


class AmbassadorLedgerCoverageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ledger-sonar",
            email="ledger-sonar@example.com",
            phone_e164="+971501234502",
            password="CustomerPass!12345",
            role=User.Role.CUSTOMER,
        )
        self.profile = AmbassadorProfile.objects.get(user=self.user)
        self.entry = PointLedger.objects.create(
            profile=self.profile,
            kind=PointLedger.Kind.ADJUST,
            points=10,
            note="coverage",
        )

    def test_point_ledger_queryset_update_is_blocked(self):
        with self.assertRaises(RuntimeError):
            PointLedger.objects.filter(pk=self.entry.pk).update(points=20)

    def test_point_ledger_queryset_delete_is_blocked(self):
        with self.assertRaises(RuntimeError):
            PointLedger.objects.filter(pk=self.entry.pk).delete()

    def test_point_ledger_existing_instance_save_is_blocked(self):
        self.entry.points = 20
        with self.assertRaises(RuntimeError):
            self.entry.save()

    def test_point_ledger_instance_delete_is_blocked(self):
        with self.assertRaises(RuntimeError):
            self.entry.delete()
