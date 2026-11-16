import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0020_order_hand_to_hand_delivery"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("invoice_number", models.CharField(db_index=True, max_length=32, unique=True)),
                ("issued_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("order_reference_snapshot", models.CharField(max_length=32)),
                ("customer_name_snapshot", models.CharField(blank=True, max_length=180)),
                ("customer_phone_snapshot", models.CharField(blank=True, max_length=32)),
                ("customer_email_snapshot", models.EmailField(blank=True, max_length=254)),
                ("currency_snapshot", models.CharField(default="AED", max_length=3)),
                ("subtotal_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount_total_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("tax_total_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("shipping_total_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("grand_total_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("paid_total_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("outstanding_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("payment_status_snapshot", models.CharField(max_length=20)),
                ("payment_method_snapshot", models.CharField(max_length=20)),
                ("payment_due_date_snapshot", models.DateField(blank=True, null=True)),
                ("delivery_method_snapshot", models.CharField(max_length=20)),
                ("delivered_at_snapshot", models.DateTimeField(blank=True, null=True)),
                ("issued_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="issued_invoices", to=settings.AUTH_USER_MODEL)),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="invoice", to="orders.order")),
            ],
            options={"ordering": ["-issued_at"]},
        ),
        migrations.CreateModel(
            name="InvoiceItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_reference_snapshot", models.CharField(blank=True, max_length=32)),
                ("sku_snapshot", models.CharField(blank=True, max_length=64)),
                ("name_ar_snapshot", models.CharField(max_length=180)),
                ("name_en_snapshot", models.CharField(max_length=180)),
                ("quantity_snapshot", models.PositiveIntegerField()),
                ("unit_price_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("discount_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("tax_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("line_total_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="items", to="orders.invoice")),
            ],
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["invoice_number"], name="invoice_number_idx"),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["issued_at"], name="invoice_issued_idx"),
        ),
    ]
