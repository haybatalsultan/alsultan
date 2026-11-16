import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="cart",
            name="contact_phone",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="cart",
            name="whatsapp_opt_in_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cart",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cart",
            name="converted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cart",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="cart",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="cart",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
    ]
