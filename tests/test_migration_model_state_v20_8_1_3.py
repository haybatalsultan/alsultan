from django.test import SimpleTestCase

from catalog.models import ProductCustodyHistory
from orders.models import DirectPaymentEntry, Order


class MigrationModelStateV20813Tests(SimpleTestCase):
    def test_deferred_payment_model_state_is_present(self):
        payment_statuses = {value for value, _ in Order.PaymentStatus.choices}
        payment_methods = {value for value, _ in Order.PaymentMethod.choices}
        self.assertIn("PARTIALLY_PAID", payment_statuses)
        self.assertIn("DEFERRED", payment_methods)
        self.assertIsNotNone(Order._meta.get_field("payment_due_date"))
        self.assertIsNotNone(Order._meta.get_field("payment_reminder_days"))
        self.assertEqual(
            DirectPaymentEntry._meta.get_field("order").remote_field.related_name,
            "direct_payments",
        )

    def test_product_custody_model_state_is_present(self):
        self.assertEqual(
            ProductCustodyHistory._meta.get_field("product").remote_field.related_name,
            "custody_history",
        )

    def test_hand_to_hand_model_state_is_present(self):
        delivery_methods = {value for value, _ in Order.DeliveryMethod.choices}
        self.assertIn("HAND_TO_HAND", delivery_methods)
        self.assertIsNotNone(Order._meta.get_field("hand_to_hand_at"))
        self.assertIsNotNone(Order._meta.get_field("hand_to_hand_by"))
