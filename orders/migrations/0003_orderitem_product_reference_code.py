from django.db import migrations, models


def refresh_product_references(apps, schema_editor):
    OrderItem = apps.get_model("orders", "OrderItem")
    for item in OrderItem.objects.select_related("product").iterator(chunk_size=500):
        if item.product and item.product.product_reference:
            reference = item.product.product_reference
        else:
            # Preserve legacy UUID information for historical rows whose product
            # no longer exists, while fitting the new 32-character snapshot field.
            reference = str(item.product_reference).replace("-", "").upper()[:32]
        OrderItem.objects.filter(pk=item.pk).update(product_reference=reference)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_product_reference"),
        ("orders", "0002_cart_followup_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderitem",
            name="product_reference",
            field=models.CharField(max_length=64),
        ),
        migrations.RunPython(refresh_product_references, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="orderitem",
            name="product_reference",
            field=models.CharField(max_length=32),
        ),
    ]
