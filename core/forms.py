from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.utils.translation import get_language

from accounts.models import SupervisorPermission
from catalog.services.image_service import validate_image
from catalog.models import Category, Material, Product, Promotion
from orders.models import Expense, Order
from core.models import StoreSetting


MANAGEMENT_INPUT_CLASS_SUFFIX = ' management-input'
SUPPORTED_IMAGE_ACCEPT = 'image/jpeg,image/png,image/webp,image/avif'

class ManagementProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name_ar",
            "name_en",
            "description_ar",
            "description_en",
            "meta_title_ar",
            "meta_title_en",
            "meta_description_ar",
            "meta_description_en",
            "category",
            "material",
            "origin",
            "color",
            "bead_count",
            "bead_size_mm",
            "weight_g",
            "shape",
            "tassel_type",
            "condition",
            "available_quantity",
            "status",
            "is_featured",
            "is_new_arrival",
            "is_best_seller",
            "verification_status",
        )
        widgets = {
            "description_ar": forms.Textarea(attrs={"rows": 4}),
            "description_en": forms.Textarea(attrs={"rows": 4}),
            "meta_description_ar": forms.Textarea(attrs={"rows": 3}),
            "meta_description_en": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, allow_status=True, allow_verification=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not allow_status:
            self.fields.pop("status", None)
        if not allow_verification:
            self.fields.pop("verification_status", None)
        elif "verification_status" in self.fields:
            # Backward-compatible and secure default: an omitted owner field
            # means "no verification claim", never CERTIFIED/INSPECTED.
            self.fields["verification_status"].required = False
            self.fields["verification_status"].initial = (
                self.instance.verification_status
                if self.instance and self.instance.pk
                else Product.VerificationStatus.NONE
            )
        category_filter = Q(is_active=True)
        material_filter = Q(is_active=True)
        if self.instance and self.instance.pk:
            category_filter |= Q(pk=self.instance.category_id)
            if self.instance.material_id:
                material_filter |= Q(pk=self.instance.material_id)
        self.fields["category"].queryset = Category.objects.filter(
            category_filter
        ).distinct()
        self.fields["material"].queryset = Material.objects.filter(
            material_filter
        ).distinct()
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + MANAGEMENT_INPUT_CLASS_SUFFIX).strip()

    def clean_verification_status(self):
        # Only present for owner forms. Missing/blank input must never create a
        # trust badge accidentally.
        return (
            self.cleaned_data.get("verification_status")
            or Product.VerificationStatus.NONE
        )

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        if (
            status == Product.Status.AVAILABLE
            and self.instance
            and self.instance.pk
            and self.instance.selling_price <= 0
        ):
            self.add_error(
                "status", "حدد سعر البيع من صفحة تسعير المالك قبل جعل المنتج متاحًا."
            )
        return cleaned


class MasterDataImageMixin:
    def _apply_media_labels(self, language_code):
        if language_code == "en":
            self.fields["image"].label = "Upload image"
            self.fields["remove_image"].label = "Remove current image"
            self.fields["image"].help_text = "JPEG, PNG, WEBP or AVIF. Maximum 5 MB."
        else:
            self.fields["image"].label = "رفع صورة"
            self.fields["remove_image"].label = "حذف الصورة الحالية"
            self.fields[
                "image"
            ].help_text = "JPEG أو PNG أو WEBP أو AVIF، وبحد أقصى 5 ميجابايت."

    def clean_image(self):
        upload = self.cleaned_data.get("image")
        if upload:
            from catalog.services.image_service import validate_image

            validate_image(upload)
        return upload


class CategoryManagementForm(MasterDataImageMixin, forms.ModelForm):
    image = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": SUPPORTED_IMAGE_ACCEPT,
                "class": "management-input",
            }
        ),
    )
    remove_image = forms.BooleanField(required=False)

    class Meta:
        model = Category
        fields = ("name_ar", "name_en", "sort_order", "is_active")

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        labels_ar = {
            "name_ar": "الاسم العربي",
            "name_en": "الاسم الإنجليزي",
            "sort_order": "الترتيب",
            "is_active": "نشط",
        }
        labels_en = {
            "name_ar": "Arabic Name",
            "name_en": "English Name",
            "sort_order": "Sort Order",
            "is_active": "Active",
        }
        labels = labels_en if language_code == "en" else labels_ar
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + MANAGEMENT_INPUT_CLASS_SUFFIX).strip()
        self._apply_media_labels(language_code)

    def clean(self):
        cleaned = super().clean()
        name_ar = (cleaned.get("name_ar") or "").strip()
        name_en = (cleaned.get("name_en") or "").strip()
        if name_ar:
            qs = Category.objects.filter(name_ar__iexact=name_ar)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("name_ar", "يوجد تصنيف بهذا الاسم العربي بالفعل.")
        if name_en:
            qs = Category.objects.filter(name_en__iexact=name_en)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "name_en", "A category with this English name already exists."
                )
        return cleaned


class MaterialManagementForm(MasterDataImageMixin, forms.ModelForm):
    image = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": SUPPORTED_IMAGE_ACCEPT,
                "class": "management-input",
            }
        ),
    )
    remove_image = forms.BooleanField(required=False)

    class Meta:
        model = Material
        fields = ("name_ar", "name_en", "sort_order", "is_active")

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        labels_ar = {
            "name_ar": "الاسم العربي",
            "name_en": "الاسم الإنجليزي",
            "sort_order": "الترتيب",
            "is_active": "نشط",
        }
        labels_en = {
            "name_ar": "Arabic Name",
            "name_en": "English Name",
            "sort_order": "Sort Order",
            "is_active": "Active",
        }
        labels = labels_en if language_code == "en" else labels_ar
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + MANAGEMENT_INPUT_CLASS_SUFFIX).strip()
        self._apply_media_labels(language_code)

    def clean(self):
        cleaned = super().clean()
        name_ar = (cleaned.get("name_ar") or "").strip()
        name_en = (cleaned.get("name_en") or "").strip()
        if name_ar:
            qs = Material.objects.filter(name_ar__iexact=name_ar)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("name_ar", "توجد خامة بهذا الاسم العربي بالفعل.")
        if name_en:
            qs = Material.objects.filter(name_en__iexact=name_en)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "name_en", "A material with this English name already exists."
                )
        return cleaned


class PricingForm(forms.ModelForm):
    discount_reason = forms.CharField(required=False, max_length=200)
    confirm_high_discount = forms.BooleanField(required=False)

    HIGH_DISCOUNT_WARNING_PERCENT = Decimal("15.00")

    class Meta:
        model = Product
        fields = ("cost_price", "selling_price", "discount_price")

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        self.language_code = str(language_code).lower()
        self.high_discount_percent = None
        self.fields["discount_reason"].label = (
            "Discount reason" if self.language_code.startswith("en") else "سبب الخصم"
        )
        self.fields["discount_reason"].help_text = (
            "Required when a direct product discount is set."
            if self.language_code.startswith("en")
            else "مطلوب عند وضع خصم مباشر على القطعة."
        )
        self.fields["confirm_high_discount"].label = (
            "I confirm this high discount is intentional"
            if self.language_code.startswith("en")
            else "أؤكد أن نسبة الخصم المرتفعة صحيحة ومقصودة"
        )

    def clean(self):
        cleaned = super().clean()
        selling = cleaned.get("selling_price")
        discount = cleaned.get("discount_price")
        if selling is not None and selling <= 0:
            self.add_error("selling_price", "سعر البيع يجب أن يكون أكبر من صفر.")
            return cleaned
        if discount is not None and selling is not None:
            reason = (cleaned.get("discount_reason") or "").strip()
            if not reason:
                self.add_error("discount_reason", "سبب الخصم مطلوب عند وضع خصم مباشر.")
            if discount >= selling:
                self.add_error("discount_price", "سعر الخصم يجب أن يكون أقل من سعر البيع.")
                return cleaned
            percent = ((selling - discount) / selling * Decimal("100")).quantize(
                Decimal("0.01")
            )
            self.high_discount_percent = percent
            if (
                percent > self.HIGH_DISCOUNT_WARNING_PERCENT
                and not cleaned.get("confirm_high_discount")
            ):
                message = (
                    f"High discount warning: {percent}% exceeds 15%. "
                    "Confirm the checkbox before saving."
                    if self.language_code.startswith("en")
                    else f"تنبيه: نسبة الخصم {percent}% وتتجاوز 15%. "
                    "راجع السعر ثم فعّل مربع التأكيد قبل الحفظ."
                )
                self.add_error("confirm_high_discount", message)
        return cleaned


class SupervisorPermissionForm(forms.ModelForm):
    class Meta:
        model = SupervisorPermission
        fields = (
            "view_products",
            "manage_master_data",
            "create_products",
            "edit_products",
            "archive_products",
            "manage_product_images",
            "view_inventory",
            "adjust_inventory",
            "view_inventory_history",
            "view_orders",
            "view_order_timeline",
            "view_abandoned_carts",
            "confirm_orders",
            "extend_reservations",
            "prepare_orders",
            "ship_orders",
            "cancel_orders",
            "mark_payment_pending",
            "mark_paid",
            "view_customers",
            "edit_customers",
            "contact_customers",
            "view_reports",
            "export_reports",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ar = get_language() != "en"

        labels_ar = {
            "view_products": "عرض المنتجات",
            "manage_master_data": "إدارة التصنيفات والخامات",
            "create_products": "إنشاء منتجات",
            "edit_products": "تعديل المنتجات",
            "archive_products": "أرشفة المنتجات",
            "manage_product_images": "إدارة صور المنتجات",
            "view_inventory": "عرض المخزون",
            "adjust_inventory": "تعديل المخزون",
            "view_inventory_history": "عرض سجل المخزون",
            "view_orders": "عرض الطلبات",
            "view_order_timeline": "عرض الخط الزمني للطلب",
            "view_abandoned_carts": "عرض السلات غير المكتملة",
            "confirm_orders": "تأكيد الطلبات",
            "extend_reservations": "تمديد حجوزات الطلبات",
            "prepare_orders": "تجهيز الطلبات",
            "ship_orders": "شحن الطلبات",
            "cancel_orders": "إلغاء الطلبات",
            "mark_payment_pending": "تعيين الدفع قيد الانتظار",
            "mark_paid": "تعيين الطلب كمدفوع",
            "view_customers": "عرض العملاء",
            "edit_customers": "تعديل بيانات العملاء",
            "contact_customers": "التواصل مع العملاء",
            "view_reports": "عرض التقارير",
            "export_reports": "تصدير التقارير",
        }
        labels_en = {
            "view_products": "View products",
            "manage_master_data": "Manage categories and materials",
            "create_products": "Create products",
            "edit_products": "Edit products",
            "archive_products": "Archive products",
            "manage_product_images": "Manage product images",
            "view_inventory": "View inventory",
            "adjust_inventory": "Adjust inventory",
            "view_inventory_history": "View inventory history",
            "view_orders": "View orders",
            "view_order_timeline": "View order timeline",
            "view_abandoned_carts": "View incomplete carts",
            "confirm_orders": "Confirm orders",
            "extend_reservations": "Extend order reservations",
            "prepare_orders": "Prepare orders",
            "ship_orders": "Ship orders",
            "cancel_orders": "Cancel orders",
            "mark_payment_pending": "Mark payment pending",
            "mark_paid": "Mark as paid",
            "view_customers": "View customers",
            "edit_customers": "Edit customers",
            "contact_customers": "Contact customers",
            "view_reports": "View reports",
            "export_reports": "Export reports",
        }
        labels = labels_ar if ar else labels_en

        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            field.widget.attrs["class"] = (
                field.widget.attrs.get("class", "") + " supervisor-permission-input"
            ).strip()


class InventoryAdjustmentForm(forms.Form):
    delta = forms.IntegerField(min_value=-9999, max_value=9999)
    reason = forms.CharField(max_length=300)


class OrderStatusForm(forms.Form):
    status = forms.ChoiceField(choices=[])

    def __init__(self, *args, order=None, **kwargs):
        from orders.models import Order

        super().__init__(*args, **kwargs)
        self.fields["status"].choices = Order.Status.choices
        if order is not None:
            self.fields["status"].initial = order.status
        self.fields["status"].widget.attrs["class"] = "management-input"


class ManualPaymentConfirmationForm(forms.Form):
    confirm_received = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "confirm_received"
        ].label = "I confirm that the funds were received and verified."
        self.fields["confirm_received"].widget.attrs["class"] = "management-checkbox"


class ReservationExtensionForm(forms.Form):
    minutes = forms.TypedChoiceField(
        choices=((15, "15"), (30, "30"), (60, "60")),
        coerce=int,
        required=True,
    )

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["minutes"].label = (
            "Extension (minutes)" if language_code == "en" else "مدة التمديد (دقيقة)"
        )
        self.fields["minutes"].widget.attrs["class"] = "management-input"


class PaymentStatusForm(forms.Form):
    payment_status = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        from orders.models import Order

        super().__init__(*args, **kwargs)
        self.fields["payment_status"].choices = Order.PaymentStatus.choices



class HandToHandDeliveryForm(forms.Form):
    confirm_handover = forms.BooleanField(required=True)
    note = forms.CharField(max_length=300, required=False)

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        is_en = str(language_code).lower().startswith("en")
        self.fields["confirm_handover"].label = (
            "I confirm the item was handed directly to the buyer."
            if is_en else "أؤكد أن القطعة تم تسليمها يدًا بيد للمشتري."
        )
        self.fields["note"].label = "Delivery note" if is_en else "ملاحظة التسليم"
        self.fields["note"].widget.attrs.update({
            "class": "management-input",
            "maxlength": "300",
            "placeholder": "Optional" if is_en else "اختياري",
        })


class ShippingDetailsForm(forms.Form):
    shipping_carrier = forms.CharField(max_length=80, required=False)
    tracking_number = forms.CharField(max_length=120, required=False)
    tracking_url = forms.URLField(max_length=700, required=False)

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        is_en = language_code == "en"
        labels = {
            "shipping_carrier": "Shipping carrier" if is_en else "شركة التوصيل",
            "tracking_number": "Tracking number" if is_en else "رقم التتبع",
            "tracking_url": "Tracking URL (HTTPS)"
            if is_en
            else "رابط التتبع الآمن (HTTPS)",
        }
        placeholders = {
            "shipping_carrier": "Aramex / EMX / Shipa / Quiqup / Manual"
            if is_en
            else "Aramex / EMX / Shipa / Quiqup / توصيل يدوي",
            "tracking_number": "AWB / tracking number"
            if is_en
            else "رقم الشحنة / التتبع",
            "tracking_url": "https://...",
        }
        for name, field in self.fields.items():
            field.label = labels[name]
            field.widget.attrs["class"] = "management-input"
            field.widget.attrs["placeholder"] = placeholders[name]

    def clean(self):
        cleaned = super().clean()
        url = (cleaned.get("tracking_url") or "").strip()
        if url and not url.lower().startswith("https://"):
            self.add_error("tracking_url", "Tracking URL must use HTTPS.")
        return cleaned


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class ProductImageUploadForm(forms.Form):
    images = MultipleFileField(
        label="Images",
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": SUPPORTED_IMAGE_ACCEPT,
                "class": "management-input",
            }
        ),
    )


class ProductImageMetadataForm(forms.Form):
    alt_text_ar = forms.CharField(max_length=180, required=False)
    alt_text_en = forms.CharField(max_length=180, required=False)
    sort_order = forms.IntegerField(min_value=0, max_value=9999)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + MANAGEMENT_INPUT_CLASS_SUFFIX).strip()


class PromotionManagementForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = (
            "name_ar",
            "name_en",
            "scope",
            "products",
            "categories",
            "discount_type",
            "discount_value",
            "gift_name_ar",
            "gift_name_en",
            "gift_quantity",
            "starts_at",
            "ends_at",
            "priority",
            "is_active",
        )
        widgets = {
            "products": forms.SelectMultiple(attrs={"size": 10}),
            "categories": forms.SelectMultiple(attrs={"size": 8}),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["products"].queryset = Product.objects.exclude(
            status=Product.Status.ARCHIVED
        ).order_by("name_ar")
        self.fields["categories"].queryset = Category.objects.filter(
            is_active=True
        ).order_by("sort_order", "name_ar")
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + MANAGEMENT_INPUT_CLASS_SUFFIX).strip()

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get("scope")
        products = cleaned.get("products")
        categories = cleaned.get("categories")
        if scope == Promotion.Scope.PRODUCTS and not products:
            self.add_error("products", "اختر منتجًا واحدًا على الأقل لهذا العرض.")
        if scope == Promotion.Scope.CATEGORIES and not categories:
            self.add_error("categories", "اختر تصنيفًا واحدًا على الأقل لهذا العرض.")

        # Prevent an owner typo from turning a product into a near-zero price.
        # Fixed discounts must remain below the cheapest product in the selected scope.
        discount_type = cleaned.get("discount_type")
        discount_value = cleaned.get("discount_value")
        if discount_type == Promotion.DiscountType.FIXED and discount_value is not None:
            applicable = Product.objects.exclude(status=Product.Status.ARCHIVED).filter(
                selling_price__gt=0
            )
            if scope == Promotion.Scope.PRODUCTS and products:
                applicable = applicable.filter(
                    pk__in=products.values_list("pk", flat=True)
                )
            elif scope == Promotion.Scope.CATEGORIES and categories:
                applicable = applicable.filter(
                    category_id__in=categories.values_list("pk", flat=True)
                )
            minimum = (
                applicable.order_by("selling_price")
                .values_list("selling_price", flat=True)
                .first()
            )
            if minimum is not None and discount_value >= minimum:
                self.add_error(
                    "discount_value",
                    "قيمة الخصم الثابت يجب أن تكون أقل من أقل سعر منتج ضمن نطاق العرض.",
                )

        instance = self.instance
        for name, value in cleaned.items():
            # Check the field name before attribute access. Accessing an M2M
            # descriptor on an unsaved Promotion raises ValueError because the
            # instance has no primary key yet.
            if name in {"products", "categories"}:
                continue
            if hasattr(instance, name):
                setattr(instance, name, value)
        try:
            instance.clean()
        except ValidationError as exc:
            for field, messages in exc.message_dict.items():
                for message in messages:
                    self.add_error(field if field in self.fields else None, message)
        return cleaned


class ReservationOverrideForm(forms.Form):
    customer = forms.CharField(
        max_length=254, label="العميل", help_text="البريد الإلكتروني أو اسم المستخدم"
    )
    max_items = forms.IntegerField(
        min_value=4, max_value=10, initial=5, label="الحد المؤقت للقطع"
    )
    reason = forms.CharField(max_length=240, required=False, label="السبب")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "management-input"


class ExpenseOrderChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.reference} — {obj.customer_name}"


class ExpenseForm(forms.ModelForm):
    order = ExpenseOrderChoiceField(queryset=Order.objects.none(), required=False)

    class Meta:
        model = Expense
        fields = (
            "category",
            "description",
            "amount",
            "incurred_on",
            "supplier",
            "invoice_reference",
            "order",
            "notes",
        )
        widgets = {
            "incurred_on": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}
            ),
            "notes": forms.Textarea(attrs={"rows": 3, "maxlength": "500"}),
        }

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        from orders.services.expense_labels import category_choices

        self.fields["category"].choices = category_choices(language_code)
        self.fields["order"].queryset = Order.objects.order_by("-created_at")
        self.fields["order"].required = False
        self.fields["order"].empty_label = "—"
        labels_ar = {
            "category": "التصنيف",
            "description": "وصف المصروف",
            "amount": "المبلغ (AED)",
            "incurred_on": "تاريخ المصروف",
            "supplier": "المورد",
            "invoice_reference": "رقم الفاتورة / المرجع",
            "order": "طلب مرتبط (اختياري)",
            "notes": "ملاحظات",
        }
        labels_en = {
            "category": "Category",
            "description": "Expense description",
            "amount": "Amount (AED)",
            "incurred_on": "Expense date",
            "supplier": "Supplier",
            "invoice_reference": "Invoice / reference",
            "order": "Linked order (optional)",
            "notes": "Notes",
        }
        labels = labels_en if str(language_code).lower().startswith("en") else labels_ar
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            field.widget.attrs["class"] = (
                field.widget.attrs.get("class", "") + MANAGEMENT_INPUT_CLASS_SUFFIX
            ).strip()

    def clean_incurred_on(self):
        from django.utils import timezone

        value = self.cleaned_data["incurred_on"]
        if value > timezone.localdate():
            raise ValidationError("لا يمكن تسجيل مصروف بتاريخ مستقبلي.")
        return value

    def clean(self):
        cleaned = super().clean()
        for key in ("description", "supplier", "invoice_reference", "notes"):
            if cleaned.get(key):
                cleaned[key] = cleaned[key].strip()
        return cleaned


class ExpenseVoidForm(forms.Form):
    reason = forms.CharField(
        max_length=300, widget=forms.Textarea(attrs={"rows": 3, "maxlength": "300"})
    )

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].label = (
            "Void reason"
            if str(language_code).lower().startswith("en")
            else "سبب إلغاء المصروف"
        )
        self.fields["reason"].widget.attrs["class"] = "management-input"

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if len(reason) < 5:
            raise ValidationError("يرجى كتابة سبب واضح للإلغاء.")
        return reason



class QuickSaleProductSearchForm(forms.Form):
    q = forms.CharField(max_length=80, required=False)

    def clean_q(self):
        value = " ".join((self.cleaned_data.get("q") or "").split())
        return value[:80]

class QuickSaleForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())
    customer_name = forms.CharField(max_length=180, required=False)
    customer_phone = forms.CharField(max_length=16, required=False)
    customer_email = forms.EmailField(required=False)
    special_discount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, initial=0
    )
    payment_method = forms.ChoiceField(choices=(
        (Order.PaymentMethod.CASH, "Cash / نقدي"),
        (Order.PaymentMethod.BANK_TRANSFER, "Bank transfer / تحويل بنكي"),
        (Order.PaymentMethod.POS, "Card / POS"),
        (Order.PaymentMethod.OTHER, "Other / أخرى"),
        (Order.PaymentMethod.DEFERRED, "Deferred / مؤجل"),
    ))
    payment_due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type":"date"}))
    payment_reminder_days = forms.IntegerField(required=False, min_value=0, max_value=30, initial=3)
    deferred_note = forms.CharField(required=False, max_length=300)
    idempotency_key = forms.CharField(max_length=100, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = (
            Product.objects.filter(status=Product.Status.AVAILABLE)
            .filter(available_quantity__gt=F("reserved_quantity"))
            .select_related("category", "material")
            .order_by("sku")
        )
        for name, field in self.fields.items():
            if name != "idempotency_key":
                field.widget.attrs["class"] = "management-input"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_method") == Order.PaymentMethod.DEFERRED:
            due = cleaned.get("payment_due_date")
            from django.utils import timezone
            if not due:
                self.add_error("payment_due_date", "تاريخ الاستحقاق مطلوب للبيع المؤجل.")
            elif due < timezone.localdate():
                self.add_error("payment_due_date", "تاريخ الاستحقاق لا يمكن أن يكون في الماضي.")
        return cleaned

    def clean_customer_phone(self):
        value = "".join(ch for ch in (self.cleaned_data.get("customer_phone") or "") if ch.isdigit() or ch == "+")
        if value and (len(value) < 7 or len(value) > 16 or value.count("+") > 1 or ("+" in value and not value.startswith("+"))):
            raise ValidationError("Invalid phone number.")
        return value

class DirectPaymentEntryForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
    )
    payment_method = forms.ChoiceField(
        choices=(
            (Order.PaymentMethod.CASH, "Cash / نقدي"),
            (Order.PaymentMethod.BANK_TRANSFER, "Bank transfer / تحويل بنكي"),
            (Order.PaymentMethod.POS, "Card / POS"),
            (Order.PaymentMethod.OTHER, "Other / أخرى"),
        )
    )
    note = forms.CharField(max_length=300, required=False)
    confirm_received = forms.BooleanField(required=True)

    def __init__(self, *args, language_code="ar", outstanding=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.language_code = str(language_code).lower()
        is_en = self.language_code.startswith("en")
        self.outstanding = outstanding
        self.fields["amount"].label = "Amount" if is_en else "مبلغ الدفعة"
        self.fields["payment_method"].label = "Payment method" if is_en else "طريقة الدفع"
        self.fields["note"].label = "Note" if is_en else "ملاحظة"
        self.fields["confirm_received"].label = (
            "I confirm that I actually received this payment."
            if is_en else "أؤكد أنني استلمت مبلغ هذه الدفعة فعليًا."
        )
        for name in ("amount", "payment_method", "note"):
            self.fields[name].widget.attrs["class"] = "management-input"
        self.fields["note"].widget.attrs["placeholder"] = (
            "Optional" if is_en else "اختياري"
        )
        if outstanding is not None:
            self.fields["amount"].widget.attrs["max"] = str(outstanding)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if self.outstanding is not None and amount > self.outstanding:
            raise ValidationError(
                "Amount exceeds the outstanding balance."
                if getattr(self, "language_code", "ar") == "en"
                else "المبلغ أكبر من الرصيد المستحق."
            )
        return amount


class ProductCustodyForm(forms.Form):
    location_name = forms.CharField(max_length=160)
    holder_name = forms.CharField(max_length=160, required=False)
    placed_on = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    note = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        is_en = str(language_code).lower().startswith("en")
        labels = {
            "location_name": "Location" if is_en else "المكان",
            "holder_name": "Held by" if is_en else "القطعة موجودة لدى",
            "placed_on": "Placed on" if is_en else "تاريخ وضع القطعة",
            "note": "Note" if is_en else "ملاحظة",
        }
        placeholders = {
            "location_name": "Shop / store / showroom..." if is_en else "المحل / المخزن / المعرض ...",
            "holder_name": "Optional" if is_en else "اختياري — اسم الشخص أو المحل",
            "note": "Optional" if is_en else "اختياري — مثال: للعرض فقط",
        }
        for name, field in self.fields.items():
            field.label = labels[name]
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " management-input").strip()
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]

    def clean_location_name(self):
        return " ".join(self.cleaned_data["location_name"].split())

    def clean_holder_name(self):
        return " ".join((self.cleaned_data.get("holder_name") or "").split())

    def clean_note(self):
        return (self.cleaned_data.get("note") or "").strip()

    def clean_placed_on(self):
        from django.utils import timezone
        value = self.cleaned_data["placed_on"]
        if value > timezone.localdate():
            raise ValidationError("لا يمكن أن يكون تاريخ وضع القطعة في المستقبل.")
        return value


class InvoiceIdentitySettingsForm(forms.ModelForm):
    logo = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/png,image/jpeg,image/webp", "class": "management-input"}
        ),
    )
    stamp = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/png,image/jpeg,image/webp", "class": "management-input"}
        ),
    )
    remove_logo = forms.BooleanField(required=False)
    remove_stamp = forms.BooleanField(required=False)

    class Meta:
        model = StoreSetting
        fields = (
            "invoice_language",
            "invoice_business_name",
            "invoice_phone",
            "invoice_email",
            "invoice_address",
            "invoice_thank_you",
            "invoice_footer_note",
            "invoice_stamp_mode",
            "invoice_show_phone",
            "invoice_show_email",
            "invoice_show_order_reference",
        )
        widgets = {
            "invoice_footer_note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, language_code="ar", **kwargs):
        super().__init__(*args, **kwargs)
        is_en = str(language_code).lower().startswith("en")
        labels_ar = {
            "invoice_language": "لغة الفاتورة الافتراضية",
            "invoice_business_name": "اسم المتجر الظاهر",
            "invoice_phone": "الهاتف",
            "invoice_email": "البريد الإلكتروني",
            "invoice_address": "العنوان",
            "invoice_thank_you": "رسالة الشكر",
            "invoice_footer_note": "ملاحظة أسفل الفاتورة",
            "invoice_stamp_mode": "إظهار الختم",
            "invoice_show_phone": "إظهار الهاتف",
            "invoice_show_email": "إظهار البريد الإلكتروني",
            "invoice_show_order_reference": "إظهار مرجع الطلب",
            "logo": "شعار الفاتورة",
            "stamp": "ختم المتجر",
            "remove_logo": "إزالة الشعار المخصص",
            "remove_stamp": "إزالة الختم",
        }
        labels_en = {
            "invoice_language": "Default invoice language",
            "invoice_business_name": "Business display name",
            "invoice_phone": "Phone",
            "invoice_email": "Email",
            "invoice_address": "Address",
            "invoice_thank_you": "Thank-you message",
            "invoice_footer_note": "Invoice footer note",
            "invoice_stamp_mode": "Stamp visibility",
            "invoice_show_phone": "Show phone",
            "invoice_show_email": "Show email",
            "invoice_show_order_reference": "Show order reference",
            "logo": "Invoice logo",
            "stamp": "Business stamp",
            "remove_logo": "Remove custom logo",
            "remove_stamp": "Remove stamp",
        }
        for name, field in self.fields.items():
            field.label = (labels_en if is_en else labels_ar).get(name, field.label)
            if not isinstance(field.widget, forms.CheckboxInput):
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (existing + " management-input").strip()
        self.fields["invoice_language"].widget = forms.Select(
            choices=(("ar", "العربية"), ("en", "English"), ("both", "العربية + English")),
            attrs={"class": "management-input"},
        )
        self.fields["invoice_stamp_mode"].widget = forms.Select(
            choices=(
                ("PAID", "عند اكتمال الدفع فقط" if not is_en else "Paid only"),
                ("ALWAYS", "دائمًا" if not is_en else "Always"),
                ("NEVER", "عدم الإظهار" if not is_en else "Never"),
            ),
            attrs={"class": "management-input"},
        )

    def clean_logo(self):
        upload = self.cleaned_data.get("logo")
        if upload:
            validate_image(upload)
        return upload

    def clean_stamp(self):
        upload = self.cleaned_data.get("stamp")
        if upload:
            validate_image(upload)
        return upload
