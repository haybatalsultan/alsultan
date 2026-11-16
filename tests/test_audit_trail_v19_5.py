from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import MFADevice, SecurityEvent, User
from core.models import AuditLog
from core.services.audit_service import audit, verify_integrity


class ComprehensiveAuditTrailV195Tests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = User.objects.create_user(
            "audit-owner-v195",
            password="VeryStrongPass!123",
            role=User.Role.OWNER,
        )
        MFADevice.objects.create(
            user=self.owner,
            secret="JBSWY3DPEHPK3PXP",
            enabled=True,
        )

    def _request(self):
        request = self.factory.post(
            "/management/test/",
            {"password": "must-not-be-logged"},
            REMOTE_ADDR="127.0.0.1",
            HTTP_USER_AGENT="Audit Test Agent",
        )
        request.user = self.owner
        request.request_id = "audit-request-v195"
        return request

    def _owner_login(self):
        self.client.login(
            username="audit-owner-v195",
            password="VeryStrongPass!123",
        )
        session = self.client.session
        session["mfa_verified_user_id"] = str(self.owner.pk)
        session.save()

    def test_audit_recursively_redacts_secrets(self):
        log = audit(
            self._request(),
            "supervisor_permissions_changed",
            self.owner,
            old={"password": "old", "nested": {"access_token": "abc"}},
            new={"secret": "xyz", "safe": "visible"},
        )
        self.assertEqual(log.old_values["password"], "[REDACTED]")
        self.assertEqual(log.old_values["nested"]["access_token"], "[REDACTED]")
        self.assertEqual(log.new_values["secret"], "[REDACTED]")
        self.assertEqual(log.new_values["safe"], "visible")

    def test_audit_records_request_context_and_actor_snapshot(self):
        log = audit(
            self._request(),
            "product_updated",
            self.owner,
            new={"status": "AVAILABLE"},
        )
        self.assertEqual(log.actor_username, self.owner.username)
        self.assertEqual(log.actor_role, User.Role.OWNER)
        self.assertEqual(log.request_id, "audit-request-v195")
        self.assertEqual(log.http_method, "POST")
        self.assertEqual(log.path, "/management/test/")
        self.assertEqual(str(log.ip_address), "127.0.0.1")

    def test_integrity_signature_detects_database_tampering(self):
        log = audit(
            self._request(),
            "pricing_changed",
            self.owner,
            old={"selling_price": "100.00"},
            new={"selling_price": "90.00"},
        )
        self.assertTrue(verify_integrity(log))

        # Simulate a lower-level record mutation. The signature must no longer
        # validate. Application ORM update/delete paths are blocked separately.
        log.new_values = {"selling_price": "1.00"}
        self.assertFalse(verify_integrity(log))

    def test_audit_log_model_cannot_be_edited_or_deleted_normally(self):
        log = audit(
            self._request(),
            "inventory_adjusted",
            self.owner,
            new={"available_quantity": 3},
        )
        log.action = "forged"
        with self.assertRaises(RuntimeError):
            log.save()
        with self.assertRaises(RuntimeError):
            log.delete()

    def test_audit_log_bulk_update_and_delete_are_blocked(self):
        log = audit(
            self._request(),
            "product_updated",
            self.owner,
            new={"status": "DRAFT"},
        )
        with self.assertRaises(RuntimeError):
            AuditLog.objects.filter(pk=log.pk).update(action="forged")
        with self.assertRaises(RuntimeError):
            AuditLog.objects.filter(pk=log.pk).delete()

    def test_security_event_cannot_be_edited_or_deleted_normally(self):
        event = SecurityEvent.objects.create(
            user=self.owner,
            event="test_security_event",
            ip_address="127.0.0.1",
        )
        event.event = "forged"
        with self.assertRaises(RuntimeError):
            event.save()
        with self.assertRaises(RuntimeError):
            event.delete()

    def test_audit_center_is_owner_only(self):
        customer = User.objects.create_user(
            "audit-customer-v195",
            password="VeryStrongPass!123",
            role=User.Role.CUSTOMER,
        )
        self.client.login(
            username="audit-customer-v195",
            password="VeryStrongPass!123",
        )
        response = self.client.get(reverse("core:management_audit"))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_open_audit_and_security_tabs(self):
        self._owner_login()
        response = self.client.get(reverse("core:management_audit"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "audit-stats-grid")

        response = self.client.get(
            reverse("core:management_audit"),
            {"view": "security"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "audit-tabs")

    def test_audit_detail_integrity_badge_is_visible(self):
        log = audit(
            self._request(),
            "promotion_created",
            self.owner,
            new={"discount_value": "10.00"},
        )
        self._owner_login()
        response = self.client.get(
            reverse("core:management_audit_detail", args=[log.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "audit-integrity")
