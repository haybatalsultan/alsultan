from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q
from django.utils import timezone

from catalog.models import Promotion

MONEY = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def _active_promotions(at=None):
    at = at or timezone.now()
    return Promotion.objects.filter(
        is_active=True,
        starts_at__lte=at,
        ends_at__gt=at,
    )


def _active_promotions_for(product, at=None):
    return (
        _active_promotions(at)
        .filter(
            Q(scope=Promotion.Scope.ALL)
            | Q(scope=Promotion.Scope.PRODUCTS, products=product)
            | Q(scope=Promotion.Scope.CATEGORIES, categories=product.category_id)
        )
        .distinct()
        .order_by("priority", "id")
    )


def _promotion_price(base_price, promotion):
    base_price = money(base_price)
    if promotion.discount_type == Promotion.DiscountType.NONE:
        return base_price
    if promotion.discount_type == Promotion.DiscountType.PERCENT:
        final = (
            base_price
            * (Decimal("100.00") - promotion.discount_value)
            / Decimal("100.00")
        )
    else:
        final = base_price - promotion.discount_value
    # Defense-in-depth only. The management form also prevents a fixed discount
    # from equaling/exceeding the cheapest product in its configured scope.
    return max(money(final), MONEY)


def _build_snapshot(product, promotions):
    base = money(product.selling_price)
    candidates = []

    # Legacy/manual per-product discount competes with promotions. Discounts
    # never stack automatically.
    if product.discount_price is not None and Decimal(product.discount_price) < base:
        candidates.append(
            {
                "source": "PRODUCT",
                "final_price": money(product.discount_price),
                "promotion": None,
                "gift_ar": "",
                "gift_en": "",
                "gift_quantity": 0,
                "priority": 65535,
            }
        )

    for promo in promotions:
        final = _promotion_price(base, promo)
        candidates.append(
            {
                "source": "PROMOTION",
                "final_price": final,
                "promotion": promo,
                "gift_ar": promo.gift_name_ar.strip(),
                "gift_en": promo.gift_name_en.strip(),
                "gift_quantity": promo.gift_quantity if promo.has_gift else 0,
                "priority": promo.priority,
            }
        )

    if candidates:
        selected = min(candidates, key=lambda x: (x["final_price"], x["priority"]))
    else:
        selected = {
            "source": "BASE",
            "final_price": base,
            "promotion": None,
            "gift_ar": "",
            "gift_en": "",
            "gift_quantity": 0,
            "priority": 65535,
        }

    selected = dict(selected)
    selected["base_price"] = base
    selected["discount_amount"] = money(base - selected["final_price"])
    selected["has_discount"] = selected["final_price"] < base
    selected["has_gift"] = bool(selected["gift_ar"] or selected["gift_en"])
    return selected


def price_snapshot(product, at=None):
    """Return the single best non-stacking price/gift snapshot for one product."""
    return _build_snapshot(product, list(_active_promotions_for(product, at=at)))


def attach_offer_snapshots(products, at=None):
    """Attach storefront offer snapshots using a bounded number of DB queries."""
    products = list(products)
    if not products:
        return products

    product_ids = [p.pk for p in products]
    category_ids = {p.category_id for p in products}
    promos = list(
        _active_promotions(at)
        .filter(
            Q(scope=Promotion.Scope.ALL)
            | Q(scope=Promotion.Scope.PRODUCTS, products__in=product_ids)
            | Q(scope=Promotion.Scope.CATEGORIES, categories__in=category_ids)
        )
        .distinct()
        .prefetch_related("products", "categories")
        .order_by("priority", "id")
    )

    promo_products = {
        promo.pk: {p.pk for p in promo.products.all()} for promo in promos
    }
    promo_categories = {
        promo.pk: {c.pk for c in promo.categories.all()} for promo in promos
    }

    for product in products:
        applicable = []
        for promo in promos:
            if (
                promo.scope == Promotion.Scope.ALL
                or promo.scope == Promotion.Scope.PRODUCTS
                and product.pk in promo_products[promo.pk]
                or promo.scope == Promotion.Scope.CATEGORIES
                and product.category_id in promo_categories[promo.pk]
            ):
                applicable.append(promo)
        product._offer_snapshot = _build_snapshot(product, applicable)
    return products
