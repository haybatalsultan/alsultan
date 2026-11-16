from django.conf import settings
from django.db import migrations, models
import django.core.validators
from decimal import Decimal

class Migration(migrations.Migration):
    dependencies=[('orders','0018_quick_sale_channel_payment_methods')]
    operations=[
      migrations.AlterField(model_name='order',name='payment_status',field=models.CharField(choices=[('UNPAID','Unpaid'),('PENDING','Pending'),('PARTIALLY_PAID','Partially paid'),('PAID','Paid'),('FAILED','Failed'),('REFUNDED','Refunded'),('PARTIAL','Partially Refunded')],default='UNPAID',db_index=True,max_length=16)),
      migrations.AlterField(model_name='order',name='payment_method',field=models.CharField(choices=[('UNSET','Not selected'),('STRIPE','Stripe'),('MANUAL','Manual / WhatsApp'),('CASH','Cash'),('BANK_TRANSFER','Bank transfer'),('POS','Card / POS'),('OTHER','Other'),('DEFERRED','Deferred')],default='UNSET',db_index=True,max_length=16)),
      migrations.AddField(model_name='order',name='payment_due_date',field=models.DateField(blank=True,db_index=True,null=True)),
      migrations.AddField(model_name='order',name='payment_reminder_days',field=models.PositiveSmallIntegerField(default=3)),
      migrations.CreateModel(name='DirectPaymentEntry',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('amount',models.DecimalField(decimal_places=2,max_digits=12,validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),('payment_method',models.CharField(choices=[('UNSET','Not selected'),('STRIPE','Stripe'),('MANUAL','Manual / WhatsApp'),('CASH','Cash'),('BANK_TRANSFER','Bank transfer'),('POS','Card / POS'),('OTHER','Other'),('DEFERRED','Deferred')],max_length=16)),('note',models.CharField(blank=True,max_length=300)),('received_at',models.DateTimeField(auto_now_add=True,db_index=True)),('order',models.ForeignKey(on_delete=models.PROTECT,related_name='direct_payments',to='orders.order')),('received_by',models.ForeignKey(on_delete=models.PROTECT,related_name='direct_payment_entries',to=settings.AUTH_USER_MODEL))])
    ]
