from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0007_cart_order_snapshots_timeline"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="delivered_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="cost_unit_snapshot",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="cost_total_snapshot",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
    ]
