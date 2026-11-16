import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0011_payment_method_and_manual_confirmation")]
    operations = [
        migrations.CreateModel(
            name="OrderNotification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("event_key", models.CharField(max_length=80)),
                (
                    "recipient_type",
                    models.CharField(
                        choices=[("ADMIN", "Admin"), ("CUSTOMER", "Customer")],
                        max_length=16,
                    ),
                ),
                ("recipient", models.EmailField(max_length=254)),
                ("sent", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="orders.order",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="ordernotification",
            constraint=models.UniqueConstraint(
                fields=("order", "event_key", "recipient_type", "recipient"),
                name="unique_order_notification",
            ),
        ),
    ]
