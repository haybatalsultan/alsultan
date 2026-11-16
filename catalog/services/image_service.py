import logging
import secrets
import warnings
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from PIL import Image

from catalog.models import Product, ProductImage

logger = logging.getLogger("haybat.security")

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "AVIF"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/avif",
}


def _configure():
    if not all(
        (
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET,
        )
    ):
        raise RuntimeError("Cloudinary is not configured.")

    import cloudinary

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def validate_image(upload):
    if not upload:
        raise ValidationError("Image file is required.")

    size = getattr(upload, "size", 0) or 0
    if size <= 0:
        raise ValidationError("Empty image file.")
    if size > settings.PRODUCT_IMAGE_MAX_BYTES:
        raise ValidationError(
            f"Image exceeds the {settings.PRODUCT_IMAGE_MAX_BYTES // (1024 * 1024)} MB limit."
        )

    content_type = (getattr(upload, "content_type", "") or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("Allowed image types: JPEG, PNG, WEBP, AVIF.")

    data = upload.read(settings.PRODUCT_IMAGE_MAX_BYTES + 1)
    upload.seek(0)
    if len(data) > settings.PRODUCT_IMAGE_MAX_BYTES:
        raise ValidationError("Image exceeds the allowed size.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            check = Image.open(BytesIO(data))
            check.verify()

            image = Image.open(BytesIO(data))
            width, height = image.size
            fmt = (image.format or "").upper()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("Image dimensions are too large.") from exc
    except Exception as exc:
        raise ValidationError("Invalid or corrupted image file.") from exc

    if fmt not in ALLOWED_FORMATS:
        raise ValidationError("Allowed image formats: JPEG, PNG, WEBP, AVIF.")
    if (
        width <= 0
        or height <= 0
        or (width * height) > settings.PRODUCT_IMAGE_MAX_PIXELS
    ):
        raise ValidationError("Image dimensions exceed the allowed limit.")

    return {
        "width": width,
        "height": height,
        "format": fmt.lower(),
        "bytes": size,
    }


def _upload_one(upload, product):
    metadata = validate_image(upload)
    _configure()
    import cloudinary.uploader

    asset_folder = f"haybatalsultan/products/{product.product_reference}"
    random_name = f"img-{secrets.token_hex(10)}"
    public_id = f"{asset_folder}/{random_name}"

    upload.seek(0)
    result = cloudinary.uploader.upload(
        upload,
        resource_type="image",
        type="upload",
        public_id=public_id,
        asset_folder=asset_folder,
        overwrite=False,
        use_filename=False,
        unique_filename=False,
        tags=["haybatalsultan", "product", product.product_reference],
        context={
            "product_reference": product.product_reference,
            "sku": product.sku,
        },
    )
    return result, metadata


def _destroy_cloudinary(public_id, *, invalidate=True):
    _configure()
    import cloudinary.uploader

    result = cloudinary.uploader.destroy(
        public_id,
        resource_type="image",
        type="upload",
        invalidate=invalidate,
    )
    status = (result or {}).get("result")
    if status not in {"ok", "not found"}:
        raise RuntimeError("Cloudinary did not confirm image deletion.")
    return result


def attach_product_images(product, uploads):
    uploads = [item for item in uploads if item]
    if not uploads:
        raise ValidationError("Choose at least one image.")

    # Validate every file before sending anything to the external service.
    for upload in uploads:
        validate_image(upload)

    existing_count = ProductImage.objects.filter(product=product).count()
    if existing_count + len(uploads) > settings.PRODUCT_IMAGE_MAX_COUNT:
        raise ValidationError(
            f"A product may contain up to {settings.PRODUCT_IMAGE_MAX_COUNT} images."
        )

    uploaded = []
    try:
        for upload in uploads:
            result, metadata = _upload_one(upload, product)
            uploaded.append((result, metadata))
    except Exception:
        for result, _ in uploaded:
            try:
                _destroy_cloudinary(result.get("public_id", ""), invalidate=True)
            except Exception as cleanup_exc:
                logger.warning(
                    "cloudinary_cleanup_failed exception_type=%s",
                    type(cleanup_exc).__name__,
                )
        raise

    created = []
    try:
        with transaction.atomic():
            locked_product = Product.objects.select_for_update().get(pk=product.pk)
            current = ProductImage.objects.filter(product=locked_product).count()
            if current + len(uploaded) > settings.PRODUCT_IMAGE_MAX_COUNT:
                raise ValidationError(
                    f"A product may contain up to {settings.PRODUCT_IMAGE_MAX_COUNT} images."
                )

            has_primary = ProductImage.objects.filter(
                product=locked_product, is_primary=True
            ).exists()
            next_order = (
                ProductImage.objects.filter(product=locked_product)
                .order_by("-sort_order")
                .values_list("sort_order", flat=True)
                .first()
                or 0
            )

            for index, (result, metadata) in enumerate(uploaded, start=1):
                image = ProductImage.objects.create(
                    product=locked_product,
                    cloudinary_public_id=result["public_id"],
                    secure_url=result["secure_url"],
                    cloudinary_asset_id=result.get("asset_id", ""),
                    width=result.get("width") or metadata["width"],
                    height=result.get("height") or metadata["height"],
                    bytes=result.get("bytes") or metadata["bytes"],
                    format=(result.get("format") or metadata["format"])[:16],
                    alt_text_ar=locked_product.name_ar,
                    alt_text_en=locked_product.name_en,
                    sort_order=next_order + index,
                    is_primary=(not has_primary and index == 1),
                )
                created.append(image)
    except Exception:
        for result, _ in uploaded:
            try:
                _destroy_cloudinary(result.get("public_id", ""), invalidate=True)
            except Exception as cleanup_exc:
                logger.warning(
                    "cloudinary_cleanup_failed exception_type=%s",
                    type(cleanup_exc).__name__,
                )
        raise

    return created


def update_image_metadata(image, *, alt_text_ar, alt_text_en, sort_order):
    image.alt_text_ar = (alt_text_ar or "").strip()[:180]
    image.alt_text_en = (alt_text_en or "").strip()[:180]
    image.sort_order = sort_order
    image.save(update_fields=["alt_text_ar", "alt_text_en", "sort_order", "updated_at"])
    return image


def set_primary_image(image):
    with transaction.atomic():
        Product.objects.select_for_update().get(pk=image.product_id)
        ProductImage.objects.filter(
            product_id=image.product_id, is_primary=True
        ).update(is_primary=False)
        ProductImage.objects.filter(pk=image.pk).update(is_primary=True)
    image.refresh_from_db()
    return image


def delete_product_image(image):
    public_id = image.cloudinary_public_id
    product_id = image.product_id
    was_primary = image.is_primary

    # If Cloudinary fails, keep the DB record so the inconsistency is visible and retryable.
    _destroy_cloudinary(public_id, invalidate=True)

    with transaction.atomic():
        Product.objects.select_for_update().get(pk=product_id)
        target = ProductImage.objects.select_for_update().get(pk=image.pk)
        target.delete()
        if was_primary:
            replacement = (
                ProductImage.objects.filter(product_id=product_id)
                .order_by("sort_order", "id")
                .first()
            )
            if replacement:
                ProductImage.objects.filter(pk=replacement.pk).update(is_primary=True)


def delivery_url(public_id, *, width, height=None, crop="limit"):
    if not public_id:
        return ""
    if not settings.CLOUDINARY_CLOUD_NAME:
        return ""

    import cloudinary

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        secure=True,
    )
    from cloudinary.utils import cloudinary_url

    transformation = {
        "width": int(width),
        "crop": crop,
        "fetch_format": "auto",
        "quality": "auto",
    }
    if height is not None:
        transformation["height"] = int(height)
        if crop == "fill":
            transformation["gravity"] = "auto"

    url, _ = cloudinary_url(
        public_id,
        secure=True,
        resource_type="image",
        type="upload",
        transformation=[transformation],
    )
    return url


def upload_master_data_image(upload, *, kind, public_id):
    """
    Upload a category/material image. The browser cannot choose the Cloudinary
    folder or public ID; both are generated by the server.
    """
    if kind not in {"categories", "materials", "invoice-logo", "invoice-stamp"}:
        raise ValidationError("Invalid media destination.")

    metadata = validate_image(upload)
    _configure()
    import cloudinary.uploader

    asset_folder = f"haybatalsultan/{kind}"
    generated_name = f"{public_id!s}-{secrets.token_hex(8)}"
    cloudinary_public_id = f"{asset_folder}/{generated_name}"

    upload.seek(0)
    result = cloudinary.uploader.upload(
        upload,
        resource_type="image",
        type="upload",
        public_id=cloudinary_public_id,
        asset_folder=asset_folder,
        overwrite=False,
        use_filename=False,
        unique_filename=False,
        tags=["haybatalsultan", "managed-media", kind],
    )
    return result, metadata


def delete_master_data_image(public_id):
    if not public_id:
        return {"result": "not found"}
    return _destroy_cloudinary(public_id, invalidate=True)
