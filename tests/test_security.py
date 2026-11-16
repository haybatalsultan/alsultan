from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import MFADevice, SupervisorPermission, User
from catalog.models import Category, Product
from tests.helpers import login_management


class SecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner", password="VeryStrongPass!123", role="OWNER"
        )
        self.supervisor = User.objects.create_user(
            "sup", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(
            user=self.supervisor, view_products=True, edit_products=True
        )
        self.customer = User.objects.create_user(
            "cust", password="VeryStrongPass!123", role="CUSTOMER"
        )
        self.cat = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah"
        )
        self.p = Product.objects.create(
            sku="HS-0001",
            name_ar="مسبحة",
            name_en="Misbah",
            category=self.cat,
            cost_price=Decimal(100),
            selling_price=Decimal(300),
            available_quantity=1,
            status="AVAILABLE",
        )

    def test_admin_not_mounted(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_supervisor_cannot_open_pricing(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        self.assertEqual(
            self.client.get(
                reverse("core:management_pricing", args=[self.p.public_id])
            ).status_code,
            403,
        )

    def test_customer_cannot_open_management(self):
        self.client.login(username="cust", password="VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_dashboard")).status_code, 403
        )

    def test_owner_cannot_be_deleted(self):
        with self.assertRaises(ValueError):
            self.owner.delete()

    def test_cost_price_not_in_storefront_html(self):
        r = self.client.get(reverse("catalog:detail", args=[self.p.public_id]))
        self.assertNotContains(r, "100.00")


class ManagementDashboardSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner-ui", password="VeryStrongPass!123", role="OWNER", first_name="Saeed"
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )
        self.supervisor = User.objects.create_user(
            "sup-ui", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(
            user=self.supervisor,
            view_orders=True,
            view_products=True,
            view_customers=False,
        )

    def test_owner_dashboard_greets_authenticated_owner_and_uses_post_logout(self):
        self.client.login(username="owner-ui", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()
        r = self.client.get(reverse("core:management_dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Saeed")
        self.assertContains(r, 'action="' + reverse("accounts:logout") + '"')
        self.assertContains(r, 'method="post"')

    def test_supervisor_dashboard_hides_owner_only_tools(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        r = self.client.get(reverse("core:management_dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, reverse("core:management_supervisors"))
        self.assertNotContains(r, reverse("core:management_audit"))
        self.assertNotContains(r, reverse("core:management_customers"))

    def test_owner_session_without_mfa_marker_is_reauthenticated(self):
        self.client.login(username="owner-ui", password="VeryStrongPass!123")
        r = self.client.get(reverse("core:management_dashboard"))
        self.assertRedirects(
            r, reverse("accounts:login"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_rejects_get(self):
        self.client.login(username="owner-ui", password="VeryStrongPass!123")
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)


class OwnerMFASecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner-mfa",
            password="VeryStrongPass!123",
            role="OWNER",
            email="owner@example.com",
        )
        self.supervisor = User.objects.create_user(
            "sup-no-mfa", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(user=self.supervisor, view_orders=True)

    def test_owner_primary_login_requires_mfa_enrollment_before_authentication(self):
        r = self.client.post(
            reverse("accounts:login"),
            {"username": "owner-mfa", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            r, reverse("accounts:mfa_setup"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.session.get("preauth_purpose"), "setup")

    def test_owner_can_enroll_then_enters_management(self):
        import pyotp

        r = self.client.post(
            reverse("accounts:login"),
            {"username": "owner-mfa", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            r, reverse("accounts:mfa_setup"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        setup_response = self.client.get(reverse("accounts:mfa_setup"))
        self.assertEqual(setup_response.status_code, 200)
        device = MFADevice.objects.get(user=self.owner)
        self.assertFalse(device.enabled)
        code = pyotp.TOTP(device.secret).now()
        r = self.client.post(reverse("accounts:mfa_setup"), {"code": code})
        self.assertRedirects(
            r, reverse("core:management_dashboard"), fetch_redirect_response=False
        )
        device.refresh_from_db()
        self.assertTrue(device.enabled)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            self.client.session.get("mfa_verified_user_id"), str(self.owner.pk)
        )

    def test_enabled_owner_requires_otp_on_every_new_login(self):
        import pyotp

        device = MFADevice.objects.create(
            user=self.owner, secret=pyotp.random_base32(), enabled=True
        )
        r = self.client.post(
            reverse("accounts:login"),
            {"username": "owner-mfa", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            r, reverse("accounts:mfa_verify"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        code = pyotp.TOTP(device.secret).now()
        r = self.client.post(reverse("accounts:mfa_verify"), {"code": code})
        self.assertRedirects(
            r, reverse("core:management_dashboard"), fetch_redirect_response=False
        )
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(
            self.client.session.get("mfa_verified_user_id"), str(self.owner.pk)
        )

    def test_old_owner_session_without_mfa_is_blocked_from_management(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse("core:management_dashboard"))
        self.assertRedirects(
            r, reverse("accounts:mfa_setup"), fetch_redirect_response=False
        )

    def test_customer_cannot_open_mfa_setup(self):
        customer = User.objects.create_user(
            "customer-mfa", password="VeryStrongPass!123", role="CUSTOMER"
        )
        self.client.force_login(customer)
        self.assertEqual(
            self.client.get(reverse("accounts:mfa_setup")).status_code, 403
        )

    def test_owner_setup_rotates_old_unconfirmed_secret_and_renders_local_qr(self):
        old = MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=False
        )
        self.client.post(
            reverse("accounts:login"),
            {"username": "owner-mfa", "password": "VeryStrongPass!123"},
        )
        r = self.client.get(reverse("accounts:mfa_setup"))
        old.refresh_from_db()
        self.assertNotEqual(old.secret, "JBSWY3DPEHPK3PXP")
        self.assertContains(r, "data:image/png;base64,")
        self.assertNotContains(r, "Provisioning URI")

    def test_cancel_mfa_setup_deletes_unconfirmed_secret_and_clears_preauth(self):
        self.client.post(
            reverse("accounts:login"),
            {"username": "owner-mfa", "password": "VeryStrongPass!123"},
        )
        self.client.get(reverse("accounts:mfa_setup"))
        self.assertTrue(
            MFADevice.objects.filter(user=self.owner, enabled=False).exists()
        )
        r = self.client.post(reverse("accounts:mfa_cancel_setup"))
        self.assertRedirects(
            r, reverse("accounts:login"), fetch_redirect_response=False
        )
        self.assertFalse(
            MFADevice.objects.filter(user=self.owner, enabled=False).exists()
        )
        self.assertNotIn("preauth_user_id", self.client.session)

    def test_cancel_mfa_setup_rejects_get(self):
        self.assertEqual(
            self.client.get(reverse("accounts:mfa_cancel_setup")).status_code, 405
        )

    def test_supervisor_primary_login_requires_mfa_enrollment_before_management(self):
        r = self.client.post(
            reverse("accounts:login"),
            {"username": "sup-no-mfa", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            r, reverse("accounts:mfa_setup"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.session.get("preauth_purpose"), "setup")

    def test_supervisor_can_enroll_mfa_then_enter_management(self):
        import pyotp

        self.client.post(
            reverse("accounts:login"),
            {"username": "sup-no-mfa", "password": "VeryStrongPass!123"},
        )
        setup = self.client.get(reverse("accounts:mfa_setup"))
        self.assertEqual(setup.status_code, 200)
        device = MFADevice.objects.get(user=self.supervisor)
        code = pyotp.TOTP(device.secret).now()
        r = self.client.post(reverse("accounts:mfa_setup"), {"code": code})
        self.assertRedirects(
            r, reverse("core:management_dashboard"), fetch_redirect_response=False
        )
        device.refresh_from_db()
        self.assertTrue(device.enabled)
        self.assertEqual(
            self.client.session.get("mfa_verified_user_id"), str(self.supervisor.pk)
        )

    def test_enabled_supervisor_requires_otp_on_every_new_login(self):
        import pyotp

        device = MFADevice.objects.create(
            user=self.supervisor, secret=pyotp.random_base32(), enabled=True
        )
        r = self.client.post(
            reverse("accounts:login"),
            {"username": "sup-no-mfa", "password": "VeryStrongPass!123"},
        )
        self.assertRedirects(
            r, reverse("accounts:mfa_verify"), fetch_redirect_response=False
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        code = pyotp.TOTP(device.secret).now()
        r = self.client.post(reverse("accounts:mfa_verify"), {"code": code})
        self.assertRedirects(
            r, reverse("core:management_dashboard"), fetch_redirect_response=False
        )
        self.assertEqual(
            self.client.session.get("mfa_verified_user_id"), str(self.supervisor.pk)
        )

    def test_old_supervisor_session_without_mfa_is_blocked_from_management(self):
        self.client.force_login(self.supervisor)
        r = self.client.get(reverse("core:management_dashboard"))
        self.assertRedirects(
            r, reverse("accounts:mfa_setup"), fetch_redirect_response=False
        )


class IncompleteCartManagementSecurityTests(TestCase):
    def setUp(self):
        from django.utils import timezone

        from orders.models import CartItem

        self.owner = User.objects.create_user(
            "owner-carts", password="VeryStrongPass!123", role="OWNER"
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )
        self.supervisor = User.objects.create_user(
            "sup-carts", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(user=self.supervisor, view_orders=True)
        cat = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-carts"
        )
        product = Product.objects.create(
            sku="HS-CARTS",
            name_ar="مسبحة",
            name_en="Misbah",
            category=cat,
            cost_price=Decimal(10),
            selling_price=Decimal(100),
            available_quantity=2,
            status="AVAILABLE",
        )
        self.cart = __import__("orders.models", fromlist=["Cart"]).Cart.objects.create(
            contact_phone="+971501234567", whatsapp_opt_in_at=timezone.now()
        )
        CartItem.objects.create(cart=self.cart, product=product, quantity=1)
        __import__("orders.models", fromlist=["Cart"]).Cart.objects.filter(
            pk=self.cart.pk
        ).update(updated_at=timezone.now() - timezone.timedelta(minutes=60))

    def test_owner_can_view_incomplete_cart_page(self):
        self.client.login(username="owner-carts", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()
        r = self.client.get(reverse("core:management_abandoned_carts"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "+971501234567")

    def test_supervisor_cannot_view_incomplete_cart_page(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_abandoned_carts")).status_code, 403
        )

    def test_management_internal_pages_use_fixed_dashboard_back_link(self):
        self.client.login(username="owner-carts", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()
        r = self.client.get(reverse("core:management_abandoned_carts"))
        self.assertContains(r, 'href="' + reverse("core:management_dashboard") + '"')


class ProductReferenceAndPaginationTests(TestCase):
    def setUp(self):
        from django.core.exceptions import ValidationError

        self.ValidationError = ValidationError
        self.owner = User.objects.create_user(
            "owner-products", password="VeryStrongPass!123", role="OWNER"
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )
        self.supervisor = User.objects.create_user(
            "sup-products", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(
            user=self.supervisor, view_products=True, edit_products=True
        )
        self.cat = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-reference"
        )
        self.product = Product.objects.create(
            sku="HS-REF-001",
            name_ar="مسبحة مرجعية",
            name_en="Reference Misbah",
            category=self.cat,
            cost_price=Decimal(125),
            selling_price=Decimal(350),
            available_quantity=1,
            status="AVAILABLE",
        )

    def _owner_login(self):
        self.client.login(username="owner-products", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    def test_product_reference_is_generated_unique_and_not_editable(self):
        other = Product.objects.create(
            sku="HS-REF-002",
            name_ar="مسبحة ثانية",
            name_en="Second Misbah",
            category=self.cat,
            cost_price=Decimal(10),
            selling_price=Decimal(50),
        )
        self.assertTrue(self.product.product_reference.startswith("HSP-"))
        self.assertNotEqual(self.product.product_reference, other.product_reference)
        original = self.product.product_reference
        self.product.product_reference = "HSP-260814-AAAAAAAA"
        with self.assertRaises(self.ValidationError):
            self.product.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_reference, original)

    def test_product_management_searches_by_reference(self):
        self._owner_login()
        r = self.client.get(
            reverse("core:management_products"), {"q": self.product.product_reference}
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.product.product_reference)
        self.assertEqual(r.context["result_count"], 1)

    def test_product_management_uses_real_pagination(self):
        for i in range(30):
            Product.objects.create(
                sku=f"HS-PAGE-{i:03d}",
                name_ar=f"منتج {i}",
                name_en=f"Product {i}",
                category=self.cat,
                cost_price=Decimal(1),
                selling_price=Decimal(10),
            )
        self._owner_login()
        first = self.client.get(reverse("core:management_products"))
        second = self.client.get(reverse("core:management_products"), {"page": 2})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(first.context["products"]), 25)
        self.assertGreaterEqual(second.context["page_obj"].number, 2)
        self.assertContains(first, "page=2")

    def test_supervisor_cannot_tamper_with_cost_price_through_product_edit(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        r = self.client.post(
            reverse("core:management_product_edit", args=[self.product.public_id]),
            {
                "sku": self.product.sku,
                "name_ar": "مسبحة معدلة",
                "name_en": "Updated Misbah",
                "category": str(self.cat.pk),
                "available_quantity": "1",
                "status": "AVAILABLE",
                "cost_price": "1.00",
                "selling_price": "1.00",
                "discount_price": "0.50",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.cost_price, Decimal(125))
        self.assertEqual(self.product.selling_price, Decimal(350))

    def test_owner_create_product_generates_reference_then_goes_to_owner_pricing(self):
        self._owner_login()
        r = self.client.post(
            reverse("core:management_product_create"),
            {
                "sku": "HS-NEW-001",
                "name_ar": "مسبحة جديدة",
                "name_en": "New Misbah",
                "category": str(self.cat.pk),
                "available_quantity": "1",
            },
        )
        created = Product.objects.get(name_en="New Misbah")
        self.assertTrue(created.product_reference.startswith("HSP-"))
        self.assertEqual(created.sku, f"HS{created.pk:05d}")
        self.assertNotEqual(created.sku, "HS-NEW-001")
        self.assertEqual(created.status, Product.Status.DRAFT)
        self.assertRedirects(
            r,
            reverse("core:management_pricing", args=[created.public_id]),
            fetch_redirect_response=False,
        )


class MasterDataSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            "owner-master", password="VeryStrongPass!123", role="OWNER"
        )
        MFADevice.objects.create(
            user=self.owner, secret="JBSWY3DPEHPK3PXP", enabled=True
        )
        self.supervisor = User.objects.create_user(
            "sup-master", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(
            user=self.supervisor, manage_master_data=True
        )
        self.customer = User.objects.create_user(
            "cust-master", password="VeryStrongPass!123", role="CUSTOMER"
        )
        self.category = Category.objects.create(
            name_ar="مسابيح", name_en="Misbah", slug="misbah-master"
        )

    def _owner_login(self):
        self.client.login(username="owner-master", password="VeryStrongPass!123")
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    def test_supervisor_with_master_data_permission_can_manage_categories_and_materials(
        self,
    ):
        from catalog.models import Material

        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_master_data")).status_code, 200
        )
        r = self.client.post(
            reverse("core:management_category_create"),
            {
                "name_ar": "كهرمان",
                "name_en": "Amber",
                "image_url": "",
                "sort_order": "10",
                "is_active": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        created = Category.objects.get(name_en="Amber")
        self.assertTrue(created.slug.startswith("amber-"))
        r = self.client.post(
            reverse("core:management_material_create"),
            {
                "name_ar": "كهرمان طبيعي",
                "name_en": "Natural Amber",
                "sort_order": "5",
                "is_active": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(
            Material.objects.filter(name_en="Natural Amber", is_active=True).exists()
        )

    def test_supervisor_without_master_data_permission_is_denied(self):
        restricted = User.objects.create_user(
            "sup-master-restricted", password="VeryStrongPass!123", role="SUPERVISOR"
        )
        SupervisorPermission.objects.create(user=restricted, manage_master_data=False)
        login_management(self.client, restricted, "VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_master_data")).status_code, 403
        )
        self.assertEqual(
            self.client.post(
                reverse("core:management_category_create"),
                {
                    "name_ar": "ممنوع",
                    "name_en": "Denied",
                    "sort_order": "0",
                    "is_active": "on",
                },
            ).status_code,
            403,
        )
        self.assertFalse(Category.objects.filter(name_en="Denied").exists())

    def test_customer_cannot_access_master_data(self):
        self.client.login(username="cust-master", password="VeryStrongPass!123")
        self.assertEqual(
            self.client.get(reverse("core:management_master_data")).status_code, 403
        )
        self.assertEqual(
            self.client.post(
                reverse("core:management_category_create"),
                {"name_ar": "X", "name_en": "X", "sort_order": "0"},
            ).status_code,
            403,
        )

    def test_archive_is_post_only_and_non_destructive(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        url = reverse("core:management_category_toggle", args=[self.category.public_id])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.category.refresh_from_db()
        self.assertFalse(self.category.is_active)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_archived_master_data_is_not_offered_for_new_products(self):
        from catalog.models import Material
        from core.forms import ManagementProductForm

        material = Material.objects.create(
            name_ar="يسر", name_en="Yusr", slug="yusr-master", is_active=False
        )
        self.category.is_active = False
        self.category.save(update_fields=["is_active"])
        form = ManagementProductForm()
        self.assertFalse(
            form.fields["category"].queryset.filter(pk=self.category.pk).exists()
        )
        self.assertFalse(
            form.fields["material"].queryset.filter(pk=material.pk).exists()
        )

    def test_owner_can_access_master_data_with_verified_mfa_session(self):
        self._owner_login()
        self.assertEqual(
            self.client.get(reverse("core:management_master_data")).status_code, 200
        )

    def test_category_slug_is_server_generated_and_immutable(self):
        from django.core.exceptions import ValidationError

        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        self.client.post(
            reverse("core:management_category_create"),
            {
                "name_ar": "نوادر",
                "name_en": "Rare Collectibles",
                "image_url": "",
                "sort_order": "0",
                "is_active": "on",
            },
        )
        item = Category.objects.get(name_en="Rare Collectibles")
        original = item.slug
        self.assertTrue(original.startswith("rare-collectibles-"))
        item.slug = "changed-by-client"
        with self.assertRaises(ValidationError):
            item.save()

    def test_category_manual_image_url_field_is_not_exposed(self):
        login_management(self.client, self.supervisor, "VeryStrongPass!123")
        r = self.client.get(reverse("core:management_category_create"))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'name="image_url"')
        self.assertNotContains(r, "Cloudinary Image URL")
        self.assertNotContains(r, "رابط صورة Cloudinary")
        self.assertContains(r, 'type="file"')
