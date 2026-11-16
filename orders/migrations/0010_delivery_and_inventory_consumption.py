from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0009_stripe_payments")]
    operations = [
        migrations.AddField(
            model_name="reservation",
            name="consumed_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_carrier",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="order",
            name="tracking_number",
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
        migrations.AddField(
            model_name="order",
            name="tracking_url",
            field=models.URLField(blank=True, max_length=700),
        ),
        migrations.AddField(
            model_name="order",
            name="shipped_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="out_for_delivery_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending Confirmation"),
                    ("CONFIRMED", "Confirmed"),
                    ("PREPARING", "Preparing"),
                    ("READY", "Ready for Delivery"),
                    ("SHIPPED", "Shipped"),
                    ("OUT_FOR_DELIVERY", "Out for Delivery"),
                    ("DELIVERED", "Delivered"),
                    ("CANCELLED", "Cancelled"),
                    ("RETURNED", "Returned"),
                ],
                db_index=True,
                default="PENDING",
                max_length=16,
            ),
        ),
    ]
