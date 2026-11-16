import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0006_orderitem_promotion_snapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="snapshot_name_ar",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="snapshot_name_en",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="snapshot_unit_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="snapshot_image_url",
            field=models.URLField(blank=True, max_length=700),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="snapshot_verification_status",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="image_url_snapshot",
            field=models.URLField(blank=True, max_length=700),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="image_public_id_snapshot",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="verification_status_snapshot",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="category_name_ar_snapshot",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="category_name_en_snapshot",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.CreateModel(
            name="OrderTimelineEvent",
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
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("ORDER_CREATED", "Order created"),
                            ("PAYMENT_CHANGED", "Payment changed"),
                            ("STATUS_CHANGED", "Status changed"),
                            ("NOTE", "Note"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("label_ar", models.CharField(max_length=180)),
                ("label_en", models.CharField(max_length=180)),
                ("from_value", models.CharField(blank=True, max_length=80)),
                ("to_value", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_timeline_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="timeline",
                        to="orders.order",
                    ),
                ),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.AddIndex(
            model_name="ordertimelineevent",
            index=models.Index(
                fields=["order", "created_at"], name="order_timeline_idx"
            ),
        ),
    ]
