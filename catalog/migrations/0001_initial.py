import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("name_ar", models.CharField(max_length=120)),
                ("name_en", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("image_url", models.URLField(blank=True, max_length=700)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Material",
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
                ("name_ar", models.CharField(max_length=120)),
                ("name_en", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Product",
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
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                ("sku", models.CharField(db_index=True, max_length=64, unique=True)),
                ("name_ar", models.CharField(max_length=180)),
                ("name_en", models.CharField(max_length=180)),
                ("description_ar", models.TextField(blank=True)),
                ("description_en", models.TextField(blank=True)),
                ("meta_title_ar", models.CharField(blank=True, max_length=180)),
                ("meta_title_en", models.CharField(blank=True, max_length=180)),
                ("meta_description_ar", models.CharField(blank=True, max_length=320)),
                ("meta_description_en", models.CharField(blank=True, max_length=320)),
                ("origin", models.CharField(blank=True, max_length=100)),
                ("color", models.CharField(blank=True, max_length=80)),
                ("bead_count", models.PositiveSmallIntegerField(blank=True, null=True)),
                (
                    "bead_size_mm",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=6, null=True
                    ),
                ),
                (
                    "weight_g",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=9, null=True
                    ),
                ),
                ("shape", models.CharField(blank=True, max_length=80)),
                ("tassel_type", models.CharField(blank=True, max_length=100)),
                ("condition", models.CharField(blank=True, max_length=100)),
                (
                    "cost_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                (
                    "selling_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                (
                    "discount_price",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=12,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                ("available_quantity", models.PositiveIntegerField(default=0)),
                ("reserved_quantity", models.PositiveIntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("AVAILABLE", "Available"),
                            ("RESERVED", "Reserved"),
                            ("SOLD", "Sold"),
                            ("ARCHIVED", "Archived"),
                        ],
                        db_index=True,
                        default="DRAFT",
                        max_length=16,
                    ),
                ),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("is_new_arrival", models.BooleanField(db_index=True, default=False)),
                ("is_best_seller", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                    ),
                ),
                (
                    "material",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.material",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("cost_price__gte", 0)), name="product_cost_gte_0"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("selling_price__gte", 0)), name="product_sell_gte_0"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("reserved_quantity__lte", models.F("available_quantity"))
                ),
                name="reserved_lte_available",
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["status", "category"], name="catalog_pro_status_00bc1c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["is_featured", "status"], name="catalog_pro_is_feat_9c07e4_idx"
            ),
        ),
        migrations.CreateModel(
            name="ProductImage",
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
                ("cloudinary_public_id", models.CharField(max_length=255, unique=True)),
                ("secure_url", models.URLField(max_length=700)),
                ("alt_text_ar", models.CharField(blank=True, max_length=180)),
                ("alt_text_en", models.CharField(blank=True, max_length=180)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.AddConstraint(
            model_name="productimage",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary", True)),
                fields=("product",),
                name="one_primary_image_per_product",
            ),
        ),
        migrations.CreateModel(
            name="WishlistItem",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlisted_by",
                        to="catalog.product",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="wishlistitem",
            constraint=models.UniqueConstraint(
                fields=("user", "product"), name="unique_wishlist_item"
            ),
        ),
        migrations.CreateModel(
            name="InventoryTransaction",
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
                    "movement_type",
                    models.CharField(
                        choices=[
                            ("ADD", "Purchase/Add"),
                            ("SALE", "Sale"),
                            ("RESERVE", "Reservation"),
                            ("RELEASE", "Reservation Release"),
                            ("ADJUST", "Manual Adjustment"),
                            ("RETURN", "Return"),
                            ("DAMAGE", "Damage"),
                            ("CORRECTION", "Correction"),
                        ],
                        max_length=16,
                    ),
                ),
                ("quantity", models.IntegerField()),
                ("before_quantity", models.IntegerField()),
                ("after_quantity", models.IntegerField()),
                (
                    "order_reference",
                    models.CharField(blank=True, db_index=True, max_length=40),
                ),
                ("reason", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inventory_transactions",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
