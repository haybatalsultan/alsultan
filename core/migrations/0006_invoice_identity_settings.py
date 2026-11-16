from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0005_store_checkout_field_config")]

    operations = [
        migrations.AddField(model_name="storesetting", name="invoice_language", field=models.CharField(default="ar", max_length=8)),
        migrations.AddField(model_name="storesetting", name="invoice_business_name", field=models.CharField(default="هيبة السلطان", max_length=120)),
        migrations.AddField(model_name="storesetting", name="invoice_phone", field=models.CharField(default="+971 50 408 4006", max_length=32)),
        migrations.AddField(model_name="storesetting", name="invoice_email", field=models.EmailField(default="info@haybatalsultan.com", max_length=254)),
        migrations.AddField(model_name="storesetting", name="invoice_address", field=models.CharField(default="أبوظبي، الإمارات العربية المتحدة", max_length=220)),
        migrations.AddField(model_name="storesetting", name="invoice_thank_you", field=models.CharField(default="شكرًا لاختياركم هيبة السلطان", max_length=220)),
        migrations.AddField(model_name="storesetting", name="invoice_footer_note", field=models.CharField(blank=True, max_length=300)),
        migrations.AddField(model_name="storesetting", name="invoice_logo_url", field=models.URLField(blank=True, max_length=700)),
        migrations.AddField(model_name="storesetting", name="invoice_logo_public_id", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="storesetting", name="invoice_stamp_url", field=models.URLField(blank=True, max_length=700)),
        migrations.AddField(model_name="storesetting", name="invoice_stamp_public_id", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="storesetting", name="invoice_stamp_mode", field=models.CharField(choices=[("PAID","Paid only"),("ALWAYS","Always"),("NEVER","Never")], default="PAID", max_length=16)),
        migrations.AddField(model_name="storesetting", name="invoice_show_phone", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="storesetting", name="invoice_show_email", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="storesetting", name="invoice_show_order_reference", field=models.BooleanField(default=True)),
    ]
