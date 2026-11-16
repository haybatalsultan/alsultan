from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0006_supervisor_order_tracking_permissions")]

    operations = [
        migrations.AddField(
            model_name="supervisorpermission",
            name="extend_reservations",
            field=models.BooleanField(default=False),
        ),
    ]
