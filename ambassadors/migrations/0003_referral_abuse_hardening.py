from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ambassadors", "0002_backfill_customer_profiles")]
    operations = [
        migrations.AlterField(
            model_name="referral",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("REVIEW", "Manual review"),
                    ("REJECTED", "Rejected"),
                    ("AWARDED", "Awarded"),
                    ("CANCELLED", "Cancelled"),
                ],
                db_index=True,
                default="PENDING",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="referral",
            name="review_reason",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="referral",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
