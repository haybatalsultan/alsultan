import secrets

from django.db import migrations, models
from django.utils import timezone

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def build_reference():
    date_part = timezone.localdate().strftime("%y%m%d")
    random_part = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"HSP-{date_part}-{random_part}"


def populate_references(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    used = set(
        Product.objects.exclude(product_reference__isnull=True).values_list(
            "product_reference", flat=True
        )
    )
    for product in Product.objects.filter(product_reference__isnull=True).iterator(
        chunk_size=500
    ):
        reference = build_reference()
        while reference in used:
            reference = build_reference()
        used.add(reference)
        Product.objects.filter(pk=product.pk).update(product_reference=reference)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="product_reference",
            field=models.CharField(
                db_index=True, editable=False, max_length=32, null=True, unique=True
            ),
        ),
        migrations.RunPython(populate_references, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="product_reference",
            field=models.CharField(
                db_index=True, editable=False, max_length=32, unique=True
            ),
        ),
    ]
