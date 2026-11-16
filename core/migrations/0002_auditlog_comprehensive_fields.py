from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="actor_role",
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="actor_username",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="category",
            field=models.CharField(blank=True, db_index=True, max_length=40),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="outcome",
            field=models.CharField(
                choices=[("SUCCESS", "Success"), ("FAILURE", "Failure")],
                db_index=True,
                default="SUCCESS",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="source",
            field=models.CharField(
                choices=[
                    ("MANAGEMENT", "Management"),
                    ("STOREFRONT", "Storefront"),
                    ("SECURITY", "Security"),
                    ("SYSTEM", "System"),
                ],
                db_index=True,
                default="MANAGEMENT",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="request_id",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="http_method",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="path",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="user_agent",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="integrity_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["category", "created_at"], name="core_auditl_categor_9d9236_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["actor_role", "created_at"],
                name="core_auditl_actor_r_926c64_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["outcome", "created_at"], name="core_auditl_outcome_e3f3fe_idx"
            ),
        ),
    ]
