import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def release_legacy_cart_holds(apps, schema_editor):
    CartItem = apps.get_model("orders", "CartItem")
    Product = apps.get_model("catalog", "Product")
    for item in CartItem.objects.filter(reserved_until__isnull=False).iterator():
        product = Product.objects.filter(pk=item.product_id).first()
        if product:
            product.reserved_quantity = max(
                0, product.reserved_quantity - item.quantity
            )
            if (
                product.status == "RESERVED"
                and product.available_quantity > product.reserved_quantity
            ):
                product.status = "AVAILABLE"
            product.save(update_fields=["reserved_quantity", "status"])
        item.reserved_until = None
        item.save(update_fields=["reserved_until"])


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0013_cartitem_reserved_until"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.RunPython(release_legacy_cart_holds, migrations.RunPython.noop),
        migrations.CreateModel(
            name="ReservationLimitOverride",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("max_items", models.PositiveSmallIntegerField()),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("reason", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "granted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="granted_reservation_overrides",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reservation_limit_overrides",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["user", "expires_at"], name="reservation_override_idx"
                    )
                ]
            },
        ),
    ]
