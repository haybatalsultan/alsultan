import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

PRODUCT_REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_product_reference():
    date_part = timezone.localdate().strftime("%y%m%d")
    random_part = "".join(secrets.choice(PRODUCT_REFERENCE_ALPHABET) for _ in range(8))
    return f"HSP-{date_part}-{random_part}"


def _master_slug(name_en, name_ar, public_id):
    base = (
        slugify(name_en or "", allow_unicode=False)
        or slugify(name_ar or "", allow_unicode=True)
        or "item"
    )
    return f"{base[:125]}-{str(public_id).replace('-', '')[:8]}"


class Category(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name_ar = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, editable=False)
    image_url = models.URLField(max_length=700, blank=True)
    image_public_id = models.CharField(max_length=300, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["sort_order", "name_en", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _master_slug(self.name_en, self.name_ar, self.public_id)
        if self.pk:
            old_slug = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("slug", flat=True)
                .first()
            )
            if old_slug and self.slug != old_slug:
                raise ValidationError({"slug": "Category slug is immutable."})
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name_ar


class Material(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name_ar = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, editable=False)
    image_url = models.URLField(max_length=700, blank=True)
    image_public_id = models.CharField(max_length=300, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["sort_order", "name_en", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _master_slug(self.name_en, self.name_ar, self.public_id)
        if self.pk:
            old_slug = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("slug", flat=True)
                .first()
            )
            if old_slug and self.slug != old_slug:
                raise ValidationError({"slug": "Material slug is immutable."})
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name_ar


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        SOLD = "SOLD", "Sold"
        ARCHIVED = "ARCHIVED", "Archived"

    public_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    product_reference = models.CharField(
        max_length=32, unique=True, editable=False, db_index=True
    )
    sku = models.CharField(
        max_length=64, unique=True, db_index=True, null=True, blank=True, editable=False
    )
    name_ar = models.CharField(max_length=180)
    name_en = models.CharField(max_length=180)
    description_ar = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    meta_title_ar = models.CharField(max_length=180, blank=True)
    meta_title_en = models.CharField(max_length=180, blank=True)
    meta_description_ar = models.CharField(max_length=320, blank=True)
    meta_description_en = models.CharField(max_length=320, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    origin = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=80, blank=True)
    bead_count = models.PositiveSmallIntegerField(null=True, blank=True)
    bead_size_mm = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    weight_g = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True
    )
    shape = models.CharField(max_length=80, blank=True)
    tassel_type = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=100, blank=True)
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    selling_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    discount_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    available_quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    is_new_arrival = models.BooleanField(default=False, db_index=True)
    is_best_seller = models.BooleanField(default=False, db_index=True)

    class VerificationStatus(models.TextChoices):
        NONE = "NONE", "No verification"
        INSPECTED = "INSPECTED", "Product inspected"
        CERTIFIED = "CERTIFIED", "Certified"

    # Owner-controlled trust claim shown on the storefront. A single enum avoids
    # contradictory states such as "public certificate" without a certificate.
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NONE,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cost_price__gte=0), name="product_cost_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(selling_price__gte=0), name="product_sell_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    reserved_quantity__lte=models.F("available_quantity")
                ),
                name="reserved_lte_available",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    verification_status__in=["NONE", "INSPECTED", "CERTIFIED"]
                ),
                name="valid_verification_status",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "category"]),
            models.Index(fields=["is_featured", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.product_reference:
            self.product_reference = generate_product_reference()

        if self.pk:
            old = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("product_reference", "sku")
                .first()
            )
            if old:
                if (
                    old["product_reference"]
                    and self.product_reference != old["product_reference"]
                ):
                    raise ValidationError(
                        {"product_reference": "Product reference is immutable."}
                    )
                if old["sku"] and self.sku != old["sku"]:
                    raise ValidationError({"sku": "SKU is immutable."})

        creating = self.pk is None
        if creating:
            # Ignore any caller-supplied SKU. New products always receive a
            # server-generated SKU derived from the database identity.
            self.sku = None

        super().save(*args, **kwargs)

        # The database-generated primary key is concurrency-safe. Building the
        # SKU from it avoids MAX()+1 race conditions under concurrent creates.
        if creating and not self.sku:
            generated_sku = f"HS{self.pk:05d}"
            updated = (
                type(self)
                .objects.filter(pk=self.pk, sku__isnull=True)
                .update(sku=generated_sku)
            )
            if updated != 1:
                raise RuntimeError("Unable to assign the automatic SKU.")
            self.sku = generated_sku

    def clean(self):
        super().clean()
        allowed = {choice for choice, _ in self.VerificationStatus.choices}
        if self.verification_status not in allowed:
            raise ValidationError(
                {"verification_status": "Invalid product verification status."}
            )

    @property
    def offer_snapshot(self):
        cached = getattr(self, "_offer_snapshot", None)
        if cached is not None:
            return cached
        from catalog.services.promotion_service import price_snapshot

        self._offer_snapshot = price_snapshot(self)
        return self._offer_snapshot

    @property
    def effective_price(self):
        return self.offer_snapshot["final_price"]

    @property
    def free_quantity(self):
        return self.available_quantity - self.reserved_quantity

    def __str__(self):
        return f"{self.product_reference} | {self.sku} - {self.name_ar}"


class ProductImage(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    cloudinary_public_id = models.CharField(max_length=255, unique=True)
    secure_url = models.URLField(max_length=700)
    cloudinary_asset_id = models.CharField(max_length=80, blank=True, db_index=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    bytes = models.PositiveIntegerField(null=True, blank=True)
    format = models.CharField(max_length=16, blank=True)
    alt_text_ar = models.CharField(max_length=180, blank=True)
    alt_text_en = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_primary=True),
                name="one_primary_image_per_product",
            )
        ]

    def _delivery_url(self, *, width, height=None, crop="limit"):
        from catalog.services.image_service import delivery_url

        return (
            delivery_url(
                self.cloudinary_public_id,
                width=width,
                height=height,
                crop=crop,
            )
            or self.secure_url
        )

    @property
    def card_url(self):
        return self._delivery_url(width=640, height=640, crop="fill")

    @property
    def thumbnail_url(self):
        return self._delivery_url(width=240, height=240, crop="fill")

    @property
    def detail_url(self):
        return self._delivery_url(width=1600, crop="limit")

    @property
    def zoom_url(self):
        # High-resolution Cloudinary delivery is generated server-side only.
        return self._delivery_url(width=2400, crop="limit")


class Promotion(models.Model):
    class Scope(models.TextChoices):
        ALL = "ALL", "All products"
        PRODUCTS = "PRODUCTS", "Selected products"
        CATEGORIES = "CATEGORIES", "Selected categories"

    class DiscountType(models.TextChoices):
        PERCENT = "PERCENT", "Percentage"
        FIXED = "FIXED", "Fixed amount"
        NONE = "NONE", "Gift only"

    public_id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    name_ar = models.CharField(max_length=180)
    name_en = models.CharField(max_length=180)
    scope = models.CharField(
        max_length=16, choices=Scope.choices, default=Scope.PRODUCTS, db_index=True
    )
    discount_type = models.CharField(
        max_length=16, choices=DiscountType.choices, default=DiscountType.PERCENT
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    gift_name_ar = models.CharField(max_length=180, blank=True)
    gift_name_en = models.CharField(max_length=180, blank=True)
    gift_quantity = models.PositiveSmallIntegerField(default=1)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    priority = models.PositiveSmallIntegerField(default=100, db_index=True)
    is_active = models.BooleanField(default=False, db_index=True)
    products = models.ManyToManyField(Product, related_name="promotions", blank=True)
    categories = models.ManyToManyField(Category, related_name="promotions", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "priority", "-created_at"]
        indexes = [
            models.Index(
                fields=["is_active", "starts_at", "ends_at"],
                name="promo_active_time_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(discount_value__gte=0),
                name="promotion_discount_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(gift_quantity__gte=1),
                name="promotion_gift_qty_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="promotion_valid_time_window",
            ),
            models.CheckConstraint(
                condition=~models.Q(discount_type="PERCENT")
                | models.Q(discount_value__lte=90),
                name="promotion_percent_lte_90",
            ),
            models.CheckConstraint(
                condition=~models.Q(discount_type="NONE") | models.Q(discount_value=0),
                name="promotion_gift_only_zero_discount",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "End time must be later than the start time."
        if (
            self.discount_type == self.DiscountType.PERCENT
            and self.discount_value > Decimal("90.00")
        ):
            errors["discount_value"] = "Percentage discount cannot exceed 90%."
        if self.discount_type == self.DiscountType.NONE and self.discount_value != 0:
            errors["discount_value"] = (
                "Gift-only promotions must have a zero discount value."
            )
        if (
            not (self.gift_name_ar.strip() or self.gift_name_en.strip())
            and self.discount_type == self.DiscountType.NONE
        ):
            errors["gift_name_ar"] = "Gift-only promotions require a gift description."
        if errors:
            raise ValidationError(errors)

    @property
    def has_gift(self):
        return bool(self.gift_name_ar.strip() or self.gift_name_en.strip())

    def __str__(self):
        return self.name_ar or self.name_en


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_wishlist_item"
            )
        ]


class InventoryTransaction(models.Model):
    class Type(models.TextChoices):
        ADD = "ADD", "Purchase/Add"
        SALE = "SALE", "Sale"
        RESERVE = "RESERVE", "Reservation"
        RELEASE = "RELEASE", "Reservation Release"
        ADJUST = "ADJUST", "Manual Adjustment"
        RETURN = "RETURN", "Return"
        DAMAGE = "DAMAGE", "Damage"
        CORRECTION = "CORRECTION", "Correction"

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="inventory_transactions"
    )
    movement_type = models.CharField(max_length=16, choices=Type.choices)
    quantity = models.IntegerField()
    before_quantity = models.IntegerField()
    after_quantity = models.IntegerField()
    order_reference = models.CharField(max_length=40, blank=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    reason = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

class ProductCustodyHistoryQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Product custody history is append-only.")
    def delete(self, *args, **kwargs):
        raise RuntimeError("Product custody history cannot be deleted.")


class ProductCustodyHistory(models.Model):
    objects = ProductCustodyHistoryQuerySet.as_manager()
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="custody_history")
    location_name = models.CharField(max_length=160)
    holder_name = models.CharField(max_length=160, blank=True)
    placed_on = models.DateField(db_index=True)
    note = models.CharField(max_length=500, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="product_custody_entries")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Product custody history is immutable.")
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise RuntimeError("Product custody history cannot be deleted.")
