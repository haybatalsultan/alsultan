from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0017_expense_accounting")]
    operations = [
        migrations.AlterField(
            model_name="order", name="payment_method",
            field=models.CharField(
                choices=[
                    ("UNSET", "Not selected"), ("STRIPE", "Stripe"),
                    ("MANUAL", "Manual / WhatsApp"), ("CASH", "Cash"),
                    ("BANK_TRANSFER", "Bank transfer"), ("POS", "Card / POS"),
                    ("OTHER", "Other"),
                ], default="UNSET", db_index=True, max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="order", name="sale_channel",
            field=models.CharField(
                choices=[("ONLINE", "Online store"), ("DIRECT", "Direct sale")],
                default="ONLINE", db_index=True, max_length=16,
            ),
        ),
    ]
