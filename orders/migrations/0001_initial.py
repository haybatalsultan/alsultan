import uuid
from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Coupon",
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
                ("code", models.CharField(max_length=40, unique=True)),
                (
                    "discount_percent",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=5
                    ),
                ),
                (
                    "max_discount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=12, null=True
                    ),
                ),
                ("active", models.BooleanField(default=True)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("usage_limit", models.PositiveIntegerField(blank=True, null=True)),
                ("used_count", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Cart",
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
                    "public_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "session_key",
                    models.CharField(blank=True, db_index=True, max_length=64),
                ),
                ("gift_option", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "coupon",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="orders.coupon",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Order",
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
                    "public_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "reference",
                    models.CharField(db_index=True, max_length=32, unique=True),
                ),
                ("customer_name", models.CharField(max_length=180)),
                ("customer_email", models.EmailField(blank=True, max_length=254)),
                ("customer_phone", models.CharField(max_length=16)),
                ("country", models.CharField(max_length=2)),
                ("emirate", models.CharField(blank=True, max_length=40)),
                ("area", models.CharField(max_length=120)),
                ("street", models.CharField(blank=True, max_length=160)),
                ("building", models.CharField(blank=True, max_length=120)),
                ("apartment_or_villa", models.CharField(blank=True, max_length=120)),
                ("additional_notes", models.CharField(blank=True, max_length=500)),
                (
                    "latitude",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        blank=True, decimal_places=6, max_digits=9, null=True
                    ),
                ),
                ("subtotal", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "discount_total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "tax_total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "shipping_total",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("grand_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="AED", max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending Confirmation"),
                            ("CONFIRMED", "Confirmed"),
                            ("PREPARING", "Preparing"),
                            ("SHIPPED", "Shipped"),
                            ("DELIVERED", "Delivered"),
                            ("CANCELLED", "Cancelled"),
                            ("RETURNED", "Returned"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=16,
                    ),
                ),
                (
                    "payment_status",
                    models.CharField(
                        choices=[
                            ("UNPAID", "Unpaid"),
                            ("PENDING", "Pending"),
                            ("PAID", "Paid"),
                            ("FAILED", "Failed"),
                            ("REFUNDED", "Refunded"),
                            ("PARTIAL", "Partially Refunded"),
                        ],
                        db_index=True,
                        default="UNPAID",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CartItem",
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
                ("quantity", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.cart",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="catalog.product",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "product"), name="unique_cart_product"
            ),
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)), name="cart_qty_gt_zero"
            ),
        ),
        migrations.CreateModel(
            name="OrderItem",
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
                ("product_reference", models.UUIDField()),
                ("sku", models.CharField(max_length=64)),
                ("name_ar", models.CharField(max_length=180)),
                ("name_en", models.CharField(max_length=180)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "discount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                (
                    "tax",
                    models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                ("quantity", models.PositiveIntegerField()),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="orders.order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="catalog.product",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)), name="order_item_qty_gt_zero"
            ),
        ),
        migrations.CreateModel(
            name="Reservation",
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
                ("quantity", models.PositiveIntegerField()),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("released_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reservations",
                        to="orders.order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to="catalog.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IdempotencyRecord",
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
                ("key", models.CharField(max_length=100, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="idempotency_records",
                        to="orders.order",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
