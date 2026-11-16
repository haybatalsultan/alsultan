import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_stripe_payment_method(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    PaymentAttempt = apps.get_model("orders", "PaymentAttempt")
    stripe_order_ids = PaymentAttempt.objects.values_list(
        "order_id", flat=True
    ).distinct()
    Order.objects.filter(id__in=stripe_order_ids).update(payment_method="STRIPE")


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0010_delivery_and_inventory_consumption"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("UNSET", "Not selected"),
                    ("STRIPE", "Stripe"),
                    ("MANUAL", "Manual / WhatsApp"),
                ],
                db_index=True,
                default="UNSET",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="manual_paid_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="manual_paid_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="manually_confirmed_orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_stripe_payment_method, migrations.RunPython.noop),
    ]
