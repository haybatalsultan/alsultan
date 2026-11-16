from django.test import SimpleTestCase

from orders.services.loyalty_service import (
    LOYALTY_TIERS,
    loyalty_label_from_count,
    loyalty_status_from_count,
)


class LoyaltyTierDefinitionV2072Tests(SimpleTestCase):
    def test_thresholds_are_exact_and_server_defined(self):
        matrix = {
            0: ("MEMBER", "عميل", 1),
            1: ("NEW", "عميل جديد", 2),
            2: ("SILVER", "عميل فضي", 4),
            3: ("SILVER", "عميل فضي", 4),
            4: ("GOLD", "عميل ذهبي", 7),
            6: ("GOLD", "عميل ذهبي", 7),
            7: ("PLATINUM", "عميل بلاتيني", 10),
            9: ("PLATINUM", "عميل بلاتيني", 10),
            10: ("ROYAL", "عميل ملكي", None),
            50: ("ROYAL", "عميل ملكي", None),
        }

        for count, (code, label_ar, next_threshold) in matrix.items():
            status = loyalty_status_from_count(count)
            self.assertEqual(status.code, code)
            self.assertEqual(status.label_ar, label_ar)
            self.assertEqual(status.next_threshold, next_threshold)

    def test_english_labels_match_new_scheme(self):
        self.assertEqual(loyalty_label_from_count(1, "en"), "New Customer")
        self.assertEqual(loyalty_label_from_count(2, "en"), "Silver Customer")
        self.assertEqual(loyalty_label_from_count(4, "en"), "Gold Customer")
        self.assertEqual(loyalty_label_from_count(7, "en"), "Platinum Customer")
        self.assertEqual(loyalty_label_from_count(10, "en"), "Royal Customer")

    def test_negative_count_is_defensively_treated_as_zero(self):
        self.assertEqual(loyalty_status_from_count(-5).code, "MEMBER")

    def test_tier_configuration_contains_no_distinguished_legacy_tier(self):
        codes = {row[1] for row in LOYALTY_TIERS}
        self.assertNotIn("DISTINGUISHED", codes)
        self.assertEqual(
            codes,
            {"MEMBER", "NEW", "SILVER", "GOLD", "PLATINUM", "ROYAL"},
        )
