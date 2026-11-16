from django.db.models import F, Q


def storefront_queryset():
    """Return only products that are genuinely purchasable on the storefront.

    A product with all stock reserved must not be presented as available even if
    ``available_quantity`` itself is greater than zero.
    """
    from catalog.models import Product

    return (
        Product.objects.filter(
            status=Product.Status.AVAILABLE,
            available_quantity__gt=F("reserved_quantity"),
        )
        .select_related("category", "material")
        .prefetch_related("images")
    )


def search_products(query="", category="", material="", available_only=True):
    if available_only:
        qs = storefront_queryset()
    else:
        product_model = __import__("catalog.models", fromlist=["Product"]).Product
        qs = product_model.objects.select_related("category", "material")

    if query:
        qs = qs.filter(
            Q(name_ar__icontains=query)
            | Q(name_en__icontains=query)
            | Q(sku__icontains=query)
            | Q(description_ar__icontains=query)
            | Q(description_en__icontains=query)
            | Q(category__name_ar__icontains=query)
            | Q(material__name_ar__icontains=query)
        )
    if category:
        qs = qs.filter(category__slug=category)
    if material:
        qs = qs.filter(material__slug=material)
    return qs
