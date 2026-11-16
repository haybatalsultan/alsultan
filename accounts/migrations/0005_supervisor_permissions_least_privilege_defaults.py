from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_customer_country_address_location_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="supervisorpermission",
            name="view_products",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="supervisorpermission",
            name="view_inventory",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="supervisorpermission",
            name="view_orders",
            field=models.BooleanField(default=False),
        ),
    ]
