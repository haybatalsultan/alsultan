from django import forms

from .models import Product


class ProductPublicFilterForm(forms.Form):
    q = forms.CharField(required=False, max_length=120)
    category = forms.CharField(required=False, max_length=140)
    material = forms.CharField(required=False, max_length=140)


class ProductOperationalForm(forms.ModelForm):
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
        )


class OwnerPricingForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("cost_price", "selling_price", "discount_price")

    def clean(self):
        data = super().clean()
        discount = data.get("discount_price")
        selling = data.get("selling_price")
        if discount is not None and selling is not None and discount > selling:
            self.add_error(
                "discount_price", "Discount price cannot exceed selling price."
            )
        return data
