from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_supervisor_permissions_least_privilege_defaults")
    ]
    operations = [
        migrations.AddField(
            model_name="supervisorpermission",
            name="manage_master_data",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="supervisorpermission",
            name="view_order_timeline",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="supervisorpermission",
            name="view_abandoned_carts",
            field=models.BooleanField(default=False),
        ),
    ]
