from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_auditlog_comprehensive_fields")]
    operations = [
        migrations.AddField(
            model_name="storesetting",
            name="notification_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="storesetting",
            name="notify_admin_new_order",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="storesetting",
            name="notify_admin_payment",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="storesetting",
            name="notify_admin_shipping",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="storesetting",
            name="notify_customer_payment",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="storesetting",
            name="notify_customer_shipping",
            field=models.BooleanField(default=True),
        ),
    ]
