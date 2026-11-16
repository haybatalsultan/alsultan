from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0019_deferred_payment_receivables"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="delivery_method",
            field=models.CharField(
                choices=[("SHIPPING", "Shipping"), ("HAND_TO_HAND", "Hand-to-hand")],
                db_index=True,
                default="SHIPPING",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="hand_to_hand_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="hand_to_hand_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="hand_to_hand_orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
