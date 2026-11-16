from django.db import migrations


def migrate_skus_to_public_hs(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    # The primary key is database-generated and unique, so this mapping is
    # deterministic and concurrency-safe for all products that already exist.
    for product in Product.objects.only("pk", "sku").order_by("pk").iterator():
        new_sku = f"HS{product.pk:05d}"
        conflict = Product.objects.exclude(pk=product.pk).filter(sku=new_sku).exists()
        if conflict:
            raise RuntimeError(
                f"Cannot migrate SKU for product {product.pk}: {new_sku} already exists."
            )
        Product.objects.filter(pk=product.pk).update(sku=new_sku)


def reverse_skus(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for product in Product.objects.only("pk").order_by("pk").iterator():
        Product.objects.filter(pk=product.pk).update(sku=f"HSA-{product.pk:06d}")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0009_product_verification_status")]
    operations = [migrations.RunPython(migrate_skus_to_public_hs, reverse_skus)]
