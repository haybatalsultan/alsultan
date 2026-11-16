from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import MFADevice, SupervisorPermission, User
from orders.models import Expense, Order, OrderItem
from orders.services.accountant_service import build_accountant_report

PASSWORD = "StrongPass!12345"


class ExpenseAccountingV2017Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner170", password=PASSWORD, role=User.Role.OWNER
        )
        MFADevice.objects.create(
            user=self.owner, secret="A" * 32, enabled=True, confirmed_at=timezone.now()
        )
        self.customer = User.objects.create_user(
            username="customer170", password=PASSWORD, role=User.Role.CUSTOMER
        )

    def login_mgmt(self, user, username):
        self.assertTrue(self.client.login(username=username, password=PASSWORD))
        session = self.client.session
        session["mfa_verified_user_id"] = str(user.pk)
        session["mfa_verified_at"] = timezone.now().timestamp()
        session.save()

    def test_supervisor_cannot_access_expenses_even_with_reports_permission(self):
        sup = User.objects.create_user(
            username="sup170", password=PASSWORD, role=User.Role.SUPERVISOR
        )
        SupervisorPermission.objects.create(
            user=sup, view_reports=True, export_reports=True
        )
        MFADevice.objects.create(
            user=sup, secret="B" * 32, enabled=True, confirmed_at=timezone.now()
        )
        self.login_mgmt(sup, "sup170")
        self.assertEqual(
            self.client.get(reverse("core:management_expenses")).status_code, 403
        )
        self.assertEqual(
            self.client.get(reverse("core:management_expense_create")).status_code, 403
        )

    def test_owner_can_create_expense_and_audit_is_recorded(self):
        self.login_mgmt(self.owner, "owner170")
        response = self.client.post(
            reverse("core:management_expense_create"),
            {
                "category": Expense.Category.BOXES,
                "description": "50 premium boxes",
                "amount": "600.00",
                "incurred_on": timezone.localdate().isoformat(),
                "supplier": "Box Supplier",
                "invoice_reference": "INV-170-1",
                "order": "",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        expense = Expense.objects.get(description="50 premium boxes")
        self.assertEqual(expense.amount, Decimal("600.00"))
        self.assertEqual(expense.created_by, self.owner)
        self.assertTrue(
            self.owner.audit_logs.filter(
                action="expense_created", object_reference=str(expense.public_id)
            ).exists()
        )

    def test_future_expense_date_is_rejected(self):
        self.login_mgmt(self.owner, "owner170")
        future = (timezone.localdate() + timezone.timedelta(days=1)).isoformat()
        response = self.client.post(
            reverse("core:management_expense_create"),
            {
                "category": Expense.Category.BAGS,
                "description": "Future bags",
                "amount": "100.00",
                "incurred_on": future,
                "supplier": "",
                "invoice_reference": "",
                "order": "",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Expense.objects.filter(description="Future bags").exists())

    def test_void_not_delete_and_excluded_from_accountant(self):
        expense = Expense.objects.create(
            category=Expense.Category.PACKAGING,
            description="Packing",
            amount=Decimal("120.00"),
            incurred_on=timezone.localdate(),
            created_by=self.owner,
            updated_by=self.owner,
        )
        self.login_mgmt(self.owner, "owner170")
        response = self.client.post(
            reverse("core:management_expense_void", args=[expense.public_id]),
            {"reason": "Duplicate invoice entry"},
        )
        self.assertEqual(response.status_code, 302)
        expense.refresh_from_db()
        self.assertEqual(expense.status, Expense.Status.VOIDED)
        self.assertEqual(Expense.objects.count(), 1)
        with self.assertRaises(RuntimeError):
            expense.delete()
        request = self.client.get(
            reverse("core:management_smart_accountant"), {"period": "today"}
        ).wsgi_request
        request.user = self.owner
        report = build_accountant_report(request)
        self.assertEqual(report["expenses_total"], Decimal("0.00"))

    def test_expenses_reduce_net_profit_without_changing_product_cost_snapshot(self):
        order = Order.objects.create(
            reference="HS-EXP-170",
            user=self.customer,
            customer_name="Customer",
            customer_phone="+971501234567",
            country="AE",
            area="Abu Dhabi",
            currency="AED",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1000.00"),
            status=Order.Status.DELIVERED,
            payment_status=Order.PaymentStatus.PAID,
            delivered_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=order,
            product=None,
            product_reference="HSP-X",
            sku="HSX",
            name_ar="اختبار",
            name_en="Test",
            quantity=1,
            unit_price=Decimal("1000.00"),
            line_total=Decimal("1000.00"),
            cost_unit_snapshot=Decimal("400.00"),
            cost_total_snapshot=Decimal("400.00"),
        )
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
        request = self.client.get(
            reverse("core:management_smart_accountant"), {"period": "today"}
        ).wsgi_request
        request.user = self.owner
        report = build_accountant_report(request)
        self.assertEqual(report["profit"], Decimal("600.00"))
        self.assertEqual(report["expenses_total"], Decimal("150.00"))
        self.assertEqual(report["net_profit"], Decimal("450.00"))
        self.assertEqual(
            report["expense_breakdown"][Expense.Category.BOXES], Decimal("100.00")
        )

    def test_voided_expense_is_immutable(self):
        expense = Expense.objects.create(
            category=Expense.Category.OTHER,
            description="Other",
            amount=Decimal("20.00"),
            incurred_on=timezone.localdate(),
            created_by=self.owner,
            updated_by=self.owner,
        )
        expense.status = Expense.Status.VOIDED
        expense.void_reason = "Entered twice"
        expense.voided_at = timezone.now()
        expense.voided_by = self.owner
        expense.save()
        expense.amount = Decimal("1.00")
        with self.assertRaises(RuntimeError):
            expense.save()
