from django.db import migrations, models


def migrate_certificate_status(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    # Preserve any existing v19 certificate claim as CERTIFIED. Products without
    # a certificate become NONE. No customer-facing metadata is retained because
    # v19.1 intentionally simplifies verification to a single owner-controlled state.
    Product.objects.filter(has_certificate=True).update(verification_status="CERTIFIED")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0008_product_certificates_promotions"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="verification_status",
            field=models.CharField(
                choices=[
                    ("NONE", "No verification"),
                    ("INSPECTED", "Product inspected"),
                    ("CERTIFIED", "Certified"),
                ],
                db_index=True,
                default="NONE",
                max_length=16,
            ),
        ),
        migrations.RunPython(migrate_certificate_status, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="product",
            name="cert_public_requires_cert",
        ),
        migrations.RemoveField(model_name="product", name="has_certificate"),
        migrations.RemoveField(model_name="product", name="certificate_issuer"),
        migrations.RemoveField(model_name="product", name="certificate_number"),
        migrations.RemoveField(model_name="product", name="certificate_date"),
        migrations.RemoveField(model_name="product", name="certificate_notes_ar"),
        migrations.RemoveField(model_name="product", name="certificate_notes_en"),
        migrations.RemoveField(model_name="product", name="certificate_public"),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    verification_status__in=["NONE", "INSPECTED", "CERTIFIED"]
                ),
                name="valid_verification_status",
            ),
        ),
    ]
