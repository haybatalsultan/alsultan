from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0004_order_policy_acceptance")]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="emirate",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="order",
            name="city",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="order",
            name="postal_code",
            field=models.CharField(blank=True, max_length=24),
        ),
    ]
