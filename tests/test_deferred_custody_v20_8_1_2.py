from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from catalog.models import Category, Product, ProductCustodyHistory
from orders.models import Order, DirectPaymentEntry
from tests.helpers import login_management

class DeferredAndCustodyTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user(username='dc-owner',password='VeryStrongPass!123',role=User.Role.OWNER)
        self.supervisor=User.objects.create_user(username='dc-super',password='VeryStrongPass!123',role=User.Role.SUPERVISOR)
        c=Category.objects.create(name_ar='مسابيح',name_en='Misbah',slug='dc-misbah')
        self.p=Product.objects.create(name_ar='قطعة مؤجلة',name_en='Deferred item',category=c,cost_price=Decimal('500'),selling_price=Decimal('1500'),available_quantity=1,status=Product.Status.AVAILABLE)
        login_management(self.client,self.owner,'VeryStrongPass!123')
    def payload(self):
        return {'product':self.p.pk,'customer_name':'Friend','customer_phone':'+971501234567','customer_email':'','special_discount':'0','payment_method':'DEFERRED','payment_due_date':(timezone.localdate()+timedelta(days=20)).isoformat(),'payment_reminder_days':'3','deferred_note':'End of month','idempotency_key':'deferred-unique-001'}
    def test_deferred_sale_is_delivered_but_not_paid(self):
        r=self.client.post(reverse('core:management_quick_sale'),self.payload()); self.assertEqual(r.status_code,302)
        o=Order.objects.get(sale_channel=Order.SaleChannel.DIRECT); self.assertEqual(o.status,Order.Status.DELIVERED); self.assertEqual(o.payment_status,Order.PaymentStatus.UNPAID); self.assertIsNone(o.manual_paid_at); self.assertIsNotNone(o.payment_due_date)
    def test_deferred_requires_due_date(self):
        d=self.payload(); d['payment_due_date']=''; r=self.client.post(reverse('core:management_quick_sale'),d); self.assertEqual(r.status_code,200); self.assertFalse(Order.objects.exists())
    def test_owner_can_record_partial_then_final_payment(self):
        self.client.post(reverse('core:management_quick_sale'),self.payload()); o=Order.objects.get()
        r=self.client.post(reverse('core:management_receivable_payment',args=[o.public_id]),{'amount':'500','payment_method':'CASH','note':'first','confirm_received':'on'}); self.assertEqual(r.status_code,302); o.refresh_from_db(); self.assertEqual(o.payment_status,Order.PaymentStatus.PARTIALLY_PAID)
        r=self.client.post(reverse('core:management_receivable_payment',args=[o.public_id]),{'amount':'1000','payment_method':'BANK_TRANSFER','note':'final','confirm_received':'on'}); self.assertEqual(r.status_code,302); o.refresh_from_db(); self.assertEqual(o.payment_status,Order.PaymentStatus.PAID); self.assertEqual(o.direct_payments.count(),2)
    def test_overpayment_is_rejected(self):
        self.client.post(reverse('core:management_quick_sale'),self.payload()); o=Order.objects.get(); r=self.client.post(reverse('core:management_receivable_payment',args=[o.public_id]),{'amount':'1600','payment_method':'CASH','confirm_received':'on'}); self.assertEqual(r.status_code,200); self.assertEqual(DirectPaymentEntry.objects.count(),0)
    def test_supervisor_cannot_view_receivables_or_custody(self):
        self.client.logout(); login_management(self.client,self.supervisor,'VeryStrongPass!123'); self.assertEqual(self.client.get(reverse('core:management_receivables')).status_code,403); self.assertEqual(self.client.get(reverse('core:management_product_custody',args=[self.p.public_id])).status_code,403)
    def test_owner_records_append_only_custody_history(self):
        r=self.client.post(reverse('core:management_product_custody',args=[self.p.public_id]),{'location_name':'Shop A','holder_name':'Ahmed','placed_on':timezone.localdate().isoformat(),'note':'Display'}); self.assertEqual(r.status_code,302); h=ProductCustodyHistory.objects.get(); self.assertEqual(h.location_name,'Shop A');
        with self.assertRaises(RuntimeError): ProductCustodyHistory.objects.filter(pk=h.pk).update(location_name='Tampered')
    def test_future_custody_date_rejected(self):
        r=self.client.post(reverse('core:management_product_custody',args=[self.p.public_id]),{'location_name':'Friend','placed_on':(timezone.localdate()+timedelta(days=1)).isoformat()}); self.assertEqual(r.status_code,200); self.assertEqual(ProductCustodyHistory.objects.count(),0)
