from django.test import TestCase
from django.urls import reverse

from accounts.models import MFADevice, User


class PromotionManagementUIV193Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "promo-ui-owner",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        MFADevice.objects.create(
            user=self.owner,
            secret="JBSWY3DPEHPK3PXP",
            enabled=True,
        )
        self.client.login(
            username="promo-ui-owner",
            password="VeryStrongPass!123",
        )
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    def test_promotions_list_uses_polished_management_components(self):
        response = self.client.get(reverse("core:management_promotions"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "promotion-overview-grid")
        self.assertContains(response, "promotion-create-btn")
        self.assertContains(response, "promotion-search-bar")
        self.assertContains(response, "management-shell")

    def test_promotion_create_uses_sectioned_responsive_form(self):
        response = self.client.get(reverse("core:management_promotion_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "promotion-form-intro")
        self.assertContains(response, "promotion-form-section")
        self.assertContains(response, "promotion-scope-panel")
        self.assertContains(response, "promotion-sticky-actions")
        self.assertContains(response, "promotion-security-note")
