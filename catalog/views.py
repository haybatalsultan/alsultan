import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from core.services.audit_service import audit

from .models import Category, Material, Product, WishlistItem
from .services.product_service import search_products


def _page(request, queryset, per_page=24):
    # Guarantee deterministic pagination even when a search service returns an
    # unordered queryset. Public IDs are only a stable tie-breaker; the
    # storefront does not expose database ordering controls to the client.
    if not queryset.ordered:
        queryset = queryset.order_by("-created_at", "-pk")
    paginator = Paginator(queryset, per_page, orphans=2)
    page_obj = paginator.get_page(request.GET.get("page"))
    page_obj.display_range = paginator.get_elided_page_range(
        page_obj.number, on_each_side=2, on_ends=1
    )
    params = request.GET.copy()
    params.pop("page", None)
    return page_obj, params.urlencode()


@require_GET
def product_list(request):
    from orders.services.cart_service import purge_expired_cart_items

    purge_expired_cart_items(limit=100)
    q = request.GET.get("q", "").strip()[:120]
    category = request.GET.get("category", "").strip()[:140]
    material = request.GET.get("material", "").strip()[:140]

    # Public navigation uses the stable alias "misbah" while Category.slug is
    # intentionally immutable and UUID-suffixed. Resolve the alias server-side
    # so desktop, mobile and home-category links always show all Misbah items.
    selected_category = category
    if category.casefold() == "misbah":
        misbah = (
            Category.objects.filter(is_active=True)
            .filter(Q(name_en__iexact="Misbah") | Q(name_ar__in=["مسابيح", "المسابيح"]))
            .only("slug")
            .first()
        )
        selected_category = misbah.slug if misbah else ""

    queryset = search_products(q, selected_category, material)
    # A complete public item code is an explicit navigation intent. Redirect
    # only on an exact match and only within the public storefront queryset.
    if q and not category and not material and re.fullmatch(r"(?i)HS\d{5,}", q):
        # Use a dedicated lightweight queryset for exact item-code navigation.
        # Do not apply .only() to search_products(), because that queryset uses
        # select_related(category, material) and Django rejects deferring those
        # traversed fields. Keep storefront visibility rules identical.
        exact_public_id = (
            Product.objects.filter(
                status=Product.Status.AVAILABLE,
                available_quantity__gt=F("reserved_quantity"),
                sku__iexact=q,
            )
            .values_list("public_id", flat=True)
            .first()
        )
        if exact_public_id:
            return redirect("catalog:detail", public_id=exact_public_id)
    page_obj, pagination_query = _page(request, queryset, 24)
    from catalog.services.promotion_service import attach_offer_snapshots

    attach_offer_snapshots(page_obj.object_list)
    return render(
        request,
        "catalog/product_list.html",
        {
            "page_obj": page_obj,
            "pagination_query": pagination_query,
            "q": q,
            "categories": Category.objects.filter(is_active=True),
            "materials": Material.objects.filter(is_active=True),
            "selected_category": selected_category,
        },
    )


@ensure_csrf_cookie
@require_GET
def product_detail(request, public_id):
    from orders.services.cart_service import purge_expired_cart_items

    purge_expired_cart_items(limit=100)
    # Keep SOLD/temporarily RESERVED product pages available by direct URL for
    # transparency and stable links, while DRAFT/ARCHIVED products remain private.
    product = get_object_or_404(
        Product.objects.select_related("category", "material").prefetch_related(
            "images"
        ),
        public_id=public_id,
        status__in=[
            Product.Status.AVAILABLE,
            Product.Status.RESERVED,
            Product.Status.SOLD,
        ],
    )
    from catalog.services.promotion_service import price_snapshot

    product._offer_snapshot = price_snapshot(product)
    sold_out = product.status == Product.Status.SOLD or product.available_quantity <= 0
    temporarily_reserved = not sold_out and product.free_quantity <= 0
    purchasable = (
        product.status == Product.Status.AVAILABLE and product.free_quantity > 0
    )
    is_wishlisted = (
        request.user.is_authenticated
        and WishlistItem.objects.filter(user=request.user, product=product).exists()
    )
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "offer": product._offer_snapshot,
            "sold_out": sold_out,
            "temporarily_reserved": temporarily_reserved,
            "purchasable": purchasable,
            "is_wishlisted": is_wishlisted,
        },
    )


@require_POST
def product_viewers(request, public_id):
    # Viewer counts are allowed only for product pages that are themselves public.
    product = get_object_or_404(
        Product,
        public_id=public_id,
        status__in=[
            Product.Status.AVAILABLE,
            Product.Status.RESERVED,
            Product.Status.SOLD,
        ],
    )
    from .services.viewer_service import (
        get_or_create_viewer_token,
        touch_product_viewer,
    )

    token = get_or_create_viewer_token(request)
    count = touch_product_viewer(product.public_id, token)
    return JsonResponse({"count": count})


@login_required
@require_POST
def wishlist_toggle(request, public_id):
    # Wishlist is intentionally independent from inventory reservation. A customer
    # may keep an available, temporarily reserved, or sold public item as a reference.
    # DRAFT/ARCHIVED products remain inaccessible to prevent IDOR-style probing.
    product = get_object_or_404(
        Product,
        public_id=public_id,
        status__in=[
            Product.Status.AVAILABLE,
            Product.Status.RESERVED,
            Product.Status.SOLD,
        ],
    )
    obj, created = WishlistItem.objects.get_or_create(
        user=request.user, product=product
    )
    if created:
        added = True
        event = "wishlist_added"
        old_state, new_state = {"wishlist": False}, {"wishlist": True}
    else:
        obj.delete()
        added = False
        event = "wishlist_removed"
        old_state, new_state = {"wishlist": True}, {"wishlist": False}

    audit(request, event, product, old=old_state, new=new_state)

    language = getattr(request, "LANGUAGE_CODE", "ar")
    if str(language).lower().startswith("en"):
        message = (
            f"{product.sku} added to your wishlist."
            if added
            else f"{product.sku} removed from your wishlist."
        )
    else:
        message = (
            f"تمت إضافة {product.sku} إلى المفضلة."
            if added
            else f"تمت إزالة {product.sku} من المفضلة."
        )

    wishlist_count = WishlistItem.objects.filter(user=request.user).count()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "wishlisted": added,
                "wishlist_count": wishlist_count,
                "message": message,
            }
        )

    messages.success(request, message)
    return redirect("catalog:detail", public_id=public_id)


@login_required
@require_GET
def wishlist(request):
    queryset = (
        request.user.wishlist_items.select_related("product", "product__category")
        .prefetch_related("product__images")
        .order_by("-created_at")
    )
    page_obj, pagination_query = _page(request, queryset, 24)
    from catalog.services.promotion_service import attach_offer_snapshots

    attach_offer_snapshots([item.product for item in page_obj.object_list])
    return render(
        request,
        "catalog/wishlist.html",
        {
            "items": page_obj.object_list,
            "page_obj": page_obj,
            "pagination_query": pagination_query,
        },
    )
