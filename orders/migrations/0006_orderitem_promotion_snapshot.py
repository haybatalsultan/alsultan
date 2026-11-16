from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0005_order_delivery_location_fields")]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="base_unit_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="promotion_label",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="gift_label",
            field=models.CharField(blank=True, max_length=180),
        ),
    ]
