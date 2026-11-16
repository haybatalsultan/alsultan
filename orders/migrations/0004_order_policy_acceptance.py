from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0003_orderitem_product_reference_code")]
    operations = [
        migrations.AddField(
            model_name="order",
            name="policy_version",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="order",
            name="policy_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
