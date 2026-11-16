from decimal import Decimal

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, SupervisorPermission, User
from orders.models import Expense

PASSWORD = "StrongPass!12345"


class ExpenseUIV20171Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner171",
            password=PASSWORD,
            role=User.Role.OWNER,
        )

        MFADevice.objects.create(
            user=self.owner,
            secret="A" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )

    def _login_mgmt(self, user, username):
        self.assertTrue(
            self.client.login(
                username=username,
                password=PASSWORD,
            )
        )

        session = self.client.session
        session["mfa_verified_user_id"] = str(user.pk)
        session["mfa_verified_at"] = timezone.now().timestamp()
        session.save()

    def test_arabic_expense_page_uses_localized_labels_and_internal_values(self):
        self._login_mgmt(
            self.owner,
            "owner171",
        )

        response = self.client.get(reverse("core:management_expenses"))

        self.assertEqual(response.status_code, 200)

        # Security/data-integrity:
        # The internal value must remain stable regardless of UI language.
        self.assertContains(
            response,
            'value="BOXES"',
        )

        # Arabic is the storefront's default language.
        self.assertContains(
            response,
            "صناديق",
        )
        self.assertContains(
            response,
            "أكياس",
        )
        self.assertContains(
            response,
            "مواد التغليف",
        )

        # English presentation must not replace the Arabic option label.
        self.assertNotContains(
            response,
            ">Boxes</option>",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_english_expense_page_keeps_english_labels(self):
        self._login_mgmt(
            self.owner,
            "owner171",
        )

        # Match the application's real language-selection mechanism.
        #
        # DefaultArabicLanguageMiddleware sets Arabic only when there is no
        # explicit language cookie. LocaleMiddleware then reads this cookie.
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"

        response = self.client.get(reverse("core:management_expenses"))

        self.assertEqual(response.status_code, 200)

        # Internal values remain language-independent.
        self.assertContains(
            response,
            'value="BOXES"',
        )

        # English presentation labels.
        self.assertContains(
            response,
            "Boxes",
        )
        self.assertContains(
            response,
            "Bags",
        )
        self.assertContains(
            response,
            "Packaging materials",
        )

    def test_category_filter_remains_allowlisted_and_server_side(self):
        Expense.objects.create(
            category=Expense.Category.BOXES,
            description="Boxes",
            amount=Decimal("100.00"),
            incurred_on=timezone.localdate(),
            created_by=self.owner,
            updated_by=self.owner,
        )

        Expense.objects.create(
            category=Expense.Category.BAGS,
            description="Bags",
            amount=Decimal("50.00"),
            incurred_on=timezone.localdate(),
            created_by=self.owner,
            updated_by=self.owner,
        )

        self._login_mgmt(
            self.owner,
            "owner171",
        )

        response = self.client.get(
            reverse("core:management_expenses"),
            {
                "category": Expense.Category.BOXES,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Boxes",
        )
        self.assertNotContains(
            response,
            "Bags",
        )

        # Security regression:
        # A crafted value must never become a dynamic ORM lookup.
        invalid = self.client.get(
            reverse("core:management_expenses"),
            {
                "category": "BOXES__contains",
            },
        )

        self.assertEqual(invalid.status_code, 200)

        # Invalid category filters are safely ignored.
        self.assertContains(
            invalid,
            "Boxes",
        )
        self.assertContains(
            invalid,
            "Bags",
        )

    def test_supervisor_cannot_access_expense_register(self):
        supervisor = User.objects.create_user(
            username="sup171",
            password=PASSWORD,
            role=User.Role.SUPERVISOR,
        )

        SupervisorPermission.objects.create(
            user=supervisor,
            view_reports=True,
        )

        MFADevice.objects.create(
            user=supervisor,
            secret="B" * 32,
            enabled=True,
            confirmed_at=timezone.now(),
        )

        self._login_mgmt(
            supervisor,
            "sup171",
        )

        response = self.client.get(reverse("core:management_expenses"))

        # Financial expense data remains owner-only even when the supervisor
        # has general report-viewing permission.
        self.assertEqual(
            response.status_code,
            403,
        )
