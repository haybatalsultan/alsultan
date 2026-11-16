from django.test import TestCase
from django.urls import reverse


class MobileOffcanvasV206Tests(TestCase):
    def test_mobile_drawer_contains_full_customer_navigation(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn('id="mobileStoreMenu"', html)
        self.assertIn("الرئيسية", html)
        self.assertIn("المسابيح", html)
        self.assertIn("الأحجار الكريمة", html)
        self.assertIn("النوادر", html)
        self.assertIn("الهدايا", html)
        self.assertIn("من نحن", html)
        self.assertIn("تواصل معنا", html)
        self.assertIn("خدماتنا الأخرى", html)

    def test_mobile_drawer_language_switch_remains_csrf_protected(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertIn('class="mobile-language-form"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_mobile_drawer_logout_is_post_not_get(self):
        from accounts.models import User

        user = User.objects.create_user(
            username="mobile-drawer-user",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.client.login(
            username="mobile-drawer-user",
            password="VeryStrongPass!123",
        )
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertIn('class="mobile-drawer-logout-form"', html)
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_mobile_drawer_does_not_add_user_controlled_navigation_urls(self):
        marker = "javascript:alert(1)"
        response = self.client.get(
            reverse("core:home"),
            {"next": marker, "menu": marker},
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertNotIn(f'href="{marker}"', html)

    def test_desktop_navigation_is_still_present(self):
        response = self.client.get(reverse("core:home"))
        html = response.content.decode("utf-8")
        self.assertIn('class="collapse main-nav-collapse"', html)
        self.assertIn('id="storeNav"', html)
