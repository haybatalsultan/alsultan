import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Product


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    max_discount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)


class Cart(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    gift_option = models.BooleanField(default=False)
    contact_phone = models.CharField(max_length=16, blank=True)
    whatsapp_opt_in_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    # Informational cart snapshot only. Checkout always recalculates price/promotion
    # from locked Product rows server-side and never trusts these values.
    snapshot_name_ar = models.CharField(max_length=180, blank=True)
    snapshot_name_en = models.CharField(max_length=180, blank=True)
    snapshot_unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    snapshot_image_url = models.URLField(max_length=700, blank=True)
    snapshot_verification_status = models.CharField(max_length=16, blank=True)
    # Server-authoritative cart reservation deadline. Client-side countdowns are display-only.
    reserved_until = models.DateTimeField(null=True, blank=True, db_index=True)
    requested_bead_count = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="cart_qty_gt_zero"
            ),
        ]


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Confirmation"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready for Delivery"
        SHIPPED = "SHIPPED", "Shipped"
        OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "Out for Delivery"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        RETURNED = "RETURNED", "Returned"

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PENDING = "PENDING", "Pending"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially paid"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        PARTIAL = "PARTIAL", "Partially Refunded"

    class PaymentMethod(models.TextChoices):
        UNSET = "UNSET", "Not selected"
        STRIPE = "STRIPE", "Stripe"
        MANUAL = "MANUAL", "Manual / WhatsApp"
        CASH = "CASH", "Cash"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
        POS = "POS", "Card / POS"
        OTHER = "OTHER", "Other"
        DEFERRED = "DEFERRED", "Deferred"

    class SaleChannel(models.TextChoices):
        ONLINE = "ONLINE", "Online store"
        DIRECT = "DIRECT", "Direct sale"

    class DeliveryMethod(models.TextChoices):
        SHIPPING = "SHIPPING", "Shipping"
        HAND_TO_HAND = "HAND_TO_HAND", "Hand-to-hand"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    customer_name = models.CharField(max_length=180)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=16)
    country = models.CharField(max_length=2)
    emirate = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=120)
    street = models.CharField(max_length=160, blank=True)
    building = models.CharField(max_length=120, blank=True)
    apartment_or_villa = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=24, blank=True)
    additional_notes = models.CharField(max_length=500, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="AED")
    policy_version = models.CharField(max_length=20, blank=True)
    policy_accepted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    payment_status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        default=PaymentMethod.UNSET,
        db_index=True,
    )
    sale_channel = models.CharField(
        max_length=16,
        choices=SaleChannel.choices,
        default=SaleChannel.ONLINE,
        db_index=True,
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.SHIPPING,
        db_index=True,
    )
    hand_to_hand_at = models.DateTimeField(null=True, blank=True, db_index=True)
    hand_to_hand_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hand_to_hand_orders",
    )
    payment_due_date = models.DateField(null=True, blank=True, db_index=True)
    payment_reminder_days = models.PositiveSmallIntegerField(default=3)
    manual_paid_at = models.DateTimeField(null=True, blank=True, db_index=True)
    manual_paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manually_confirmed_orders",
    )
    shipping_carrier = models.CharField(max_length=80, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True, db_index=True)
    tracking_url = models.URLField(max_length=700, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True, db_index=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True, db_index=True)
    delivered_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


class ExpenseQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Expenses must be changed through validated model saves.")

    def delete(self, *args, **kwargs):
        raise RuntimeError("Expenses cannot be deleted. Void the expense instead.")


class Expense(models.Model):
    class Category(models.TextChoices):
        BOXES = "BOXES", "Boxes"
        BAGS = "BAGS", "Bags"
        PACKAGING = "PACKAGING", "Packaging materials"
        CARDS_LABELS = "CARDS_LABELS", "Cards & labels"
        SHIPPING_DELIVERY = "SHIPPING_DELIVERY", "Shipping & delivery"
        MARKETING = "MARKETING", "Marketing"
        SUBSCRIPTIONS = "SUBSCRIPTIONS", "Subscriptions & services"
        PAYMENT_FEES = "PAYMENT_FEES", "Payment fees"
        OFFICE = "OFFICE", "Office & operations"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        VOIDED = "VOIDED", "Voided"

    objects = ExpenseQuerySet.as_manager()
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.CharField(max_length=32, choices=Category.choices, db_index=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    incurred_on = models.DateField(db_index=True)
    supplier = models.CharField(max_length=120, blank=True)
    invoice_reference = models.CharField(max_length=80, blank=True, db_index=True)
    notes = models.CharField(max_length=500, blank=True)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="expenses",
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_expenses",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_expenses",
    )
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="voided_expenses",
    )
    void_reason = models.CharField(max_length=300, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-incurred_on", "-created_at"]
        indexes = [
            models.Index(
                fields=["status", "incurred_on"], name="expense_status_date_idx"
            ),
            models.Index(
                fields=["category", "incurred_on"], name="expense_category_date_idx"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(("amount__gt", 0)),
                name="expense_amount_gt_zero",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        ("status", "ACTIVE"),
                        ("voided_at__isnull", True),
                        ("voided_by__isnull", True),
                        ("void_reason", ""),
                    )
                    | (
                        models.Q(
                            ("status", "VOIDED"),
                            ("voided_at__isnull", False),
                            ("voided_by__isnull", False),
                        )
                        & ~models.Q(("void_reason", ""))
                    )
                ),
                name="expense_void_state_consistent",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("status", "voided_at", "void_reason", "voided_by_id")
                .first()
            )
            if old and old["status"] == self.Status.VOIDED:
                immutable = (
                    "category",
                    "description",
                    "amount",
                    "incurred_on",
                    "supplier",
                    "invoice_reference",
                    "notes",
                    "order_id",
                    "status",
                    "voided_at",
                    "void_reason",
                    "voided_by_id",
                )
                original = type(self).objects.get(pk=self.pk)
                if any(getattr(original, f) != getattr(self, f) for f in immutable):
                    raise RuntimeError("Voided expenses are immutable.")
        if self.status == self.Status.ACTIVE and (
            self.voided_at or self.voided_by_id or self.void_reason
        ):
            raise ValueError("Active expenses cannot contain void metadata.")
        if self.status == self.Status.VOIDED and (
            not self.voided_at or not self.void_reason.strip() or not self.voided_by_id
        ):
            raise ValueError("Voided expenses require reason, timestamp and owner.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Expenses cannot be deleted. Void the expense instead.")


class ProtectedOrderItemQuerySet(models.QuerySet):
    _financial_fields = {"cost_unit_snapshot", "cost_total_snapshot"}

    def update(self, **kwargs):
        if self._financial_fields.intersection(kwargs):
            raise RuntimeError(
                "Financial order snapshots cannot be updated through application ORM."
            )
        return super().update(**kwargs)


class OrderItem(models.Model):
    objects = ProtectedOrderItemQuerySet.as_manager()
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )
    product_reference = models.CharField(max_length=32)
    sku = models.CharField(max_length=64)
    name_ar = models.CharField(max_length=180)
    name_en = models.CharField(max_length=180)
    base_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    promotion_label = models.CharField(max_length=180, blank=True)
    gift_label = models.CharField(max_length=180, blank=True)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    # Immutable proof of what the customer actually selected at checkout.
    image_url_snapshot = models.URLField(max_length=700, blank=True)
    image_public_id_snapshot = models.CharField(max_length=255, blank=True)
    verification_status_snapshot = models.CharField(max_length=16, blank=True)
    category_name_ar_snapshot = models.CharField(max_length=120, blank=True)
    category_name_en_snapshot = models.CharField(max_length=120, blank=True)
    # Owner-only historical accounting snapshots. Null means a legacy order was
    # created before v20.7, so the accountant must not invent a historical cost.
    cost_unit_snapshot = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    cost_total_snapshot = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    original_bead_count_snapshot = models.PositiveSmallIntegerField(null=True, blank=True)
    requested_bead_count_snapshot = models.PositiveSmallIntegerField(null=True, blank=True)
    bead_adjustment_completed_at = models.DateTimeField(null=True, blank=True)
    bead_adjustment_completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="completed_bead_adjustments",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="order_item_qty_gt_zero"
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("cost_unit_snapshot", "cost_total_snapshot")
                .first()
            )
            if old and (
                old["cost_unit_snapshot"] != self.cost_unit_snapshot
                or old["cost_total_snapshot"] != self.cost_total_snapshot
            ):
                raise RuntimeError("Financial order snapshots are immutable.")
        return super().save(*args, **kwargs)


class ImmutableTimelineQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError(
            "Order timeline events cannot be updated through application ORM."
        )

    def delete(self, *args, **kwargs):
        raise RuntimeError(
            "Order timeline events cannot be deleted through application ORM."
        )


class OrderTimelineEvent(models.Model):
    objects = ImmutableTimelineQuerySet.as_manager()

    class Kind(models.TextChoices):
        ORDER_CREATED = "ORDER_CREATED", "Order created"
        PAYMENT_CHANGED = "PAYMENT_CHANGED", "Payment changed"
        STATUS_CHANGED = "STATUS_CHANGED", "Status changed"
        NOTE = "NOTE", "Note"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="timeline")
    kind = models.CharField(max_length=32, choices=Kind.choices, db_index=True)
    label_ar = models.CharField(max_length=180)
    label_en = models.CharField(max_length=180)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_timeline_events",
    )
    from_value = models.CharField(max_length=80, blank=True)
    to_value = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["order", "created_at"], name="order_timeline_idx")
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Order timeline events are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Order timeline events cannot be deleted.")


class Reservation(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="reservations"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="reservations"
    )
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField(db_index=True)
    released_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class IdempotencyRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    key = models.CharField(max_length=100, unique=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="idempotency_records"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class CheckoutReservationGuard(models.Model):
    identity_key = models.CharField(max_length=96, unique=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrderNotification(models.Model):
    class RecipientType(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CUSTOMER = "CUSTOMER", "Customer"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="notifications"
    )
    event_key = models.CharField(max_length=80)
    recipient_type = models.CharField(max_length=16, choices=RecipientType.choices)
    recipient = models.EmailField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "event_key", "recipient_type", "recipient"],
                name="unique_order_notification",
            )
        ]


class PaymentAttempt(models.Model):
    class Status(models.TextChoices):
        CREATING = "CREATING", "Creating"
        OPEN = "OPEN", "Open"
        PROCESSING = "PROCESSING", "Processing"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        EXPIRED = "EXPIRED", "Expired"
        PARTIAL = "PARTIAL", "Partially refunded"
        REFUNDED = "REFUNDED", "Refunded"

    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="payment_attempts"
    )
    attempt_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checkout_session_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    payment_intent_id = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.CREATING, db_index=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="AED")
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


class StripeWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120, db_index=True)
    processed_at = models.DateTimeField(auto_now_add=True, db_index=True)


class ReservationLimitOverride(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservation_limit_overrides",
    )
    max_items = models.PositiveSmallIntegerField()
    expires_at = models.DateTimeField(db_index=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_reservation_overrides",
    )
    reason = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"], name="reservation_override_idx")
        ]


class ReservationLimitRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservation_limit_requests",
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservation_limit_requests",
    )
    requested_items = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reservation_limit_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"], name="reservation_req_status_idx"
            ),
            models.Index(fields=["user", "status"], name="reservation_req_user_idx"),
        ]

class DirectPaymentEntryQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Direct payment entries are append-only.")
    def delete(self, *args, **kwargs):
        raise RuntimeError("Direct payment entries cannot be deleted.")


class DirectPaymentEntry(models.Model):
    objects = DirectPaymentEntryQuerySet.as_manager()
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="direct_payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_method = models.CharField(max_length=16, choices=Order.PaymentMethod.choices)
    note = models.CharField(max_length=300, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="direct_payment_entries")
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Direct payment entries are immutable.")
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise RuntimeError("Direct payment entries cannot be deleted.")


class ImmutableInvoiceQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Invoices are immutable snapshots.")

    def delete(self, *args, **kwargs):
        raise RuntimeError("Invoices cannot be deleted.")


class Invoice(models.Model):
    objects = ImmutableInvoiceQuerySet.as_manager()

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="invoice",
    )
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice_number = models.CharField(max_length=32, unique=True, db_index=True)
    issued_at = models.DateTimeField(auto_now_add=True, db_index=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issued_invoices",
    )

    order_reference_snapshot = models.CharField(max_length=32)
    customer_name_snapshot = models.CharField(max_length=180, blank=True)
    customer_phone_snapshot = models.CharField(max_length=32, blank=True)
    customer_email_snapshot = models.EmailField(blank=True)
    currency_snapshot = models.CharField(max_length=3, default="AED")
    subtotal_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    discount_total_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    tax_total_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_total_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    grand_total_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    paid_total_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    outstanding_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status_snapshot = models.CharField(max_length=20)
    payment_method_snapshot = models.CharField(max_length=20)
    payment_due_date_snapshot = models.DateField(null=True, blank=True)
    delivery_method_snapshot = models.CharField(max_length=20)
    delivered_at_snapshot = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["invoice_number"], name="invoice_number_idx"),
            models.Index(fields=["issued_at"], name="invoice_issued_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Invoices are immutable snapshots.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Invoices cannot be deleted.")


class ImmutableInvoiceItemQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise RuntimeError("Invoice items are immutable snapshots.")

    def delete(self, *args, **kwargs):
        raise RuntimeError("Invoice items cannot be deleted.")


class InvoiceItem(models.Model):
    objects = ImmutableInvoiceItemQuerySet.as_manager()

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="items",
    )
    product_reference_snapshot = models.CharField(max_length=32, blank=True)
    sku_snapshot = models.CharField(max_length=64, blank=True)
    name_ar_snapshot = models.CharField(max_length=180)
    name_en_snapshot = models.CharField(max_length=180)
    quantity_snapshot = models.PositiveIntegerField()
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    discount_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    original_bead_count_snapshot = models.PositiveSmallIntegerField(null=True, blank=True)
    requested_bead_count_snapshot = models.PositiveSmallIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise RuntimeError("Invoice items are immutable snapshots.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("Invoice items cannot be deleted.")
