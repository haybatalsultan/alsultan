from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from catalog.models import Category, Material, Product
from catalog.services.image_service import attach_product_images, update_image_metadata

BARREL_SHAPE_AR = 'برميلي'
CLASSIC_TASSEL_AR = 'كركوشة كلاسيكية'
OVAL_SHAPE_AR = 'بيضاوي'
ROUND_SHAPE_AR = 'دائري'
SILK_TASSEL_AR = 'كركوشة حرير'
LUXURY_TASSEL_AR = 'كركوشة فاخرة'
AGED_IVORY_AR = 'عاجي معتّق'
LIGHT_IVORY_AR = 'عاجي فاتح'
WARM_IVORY_AR = 'عاجي دافئ'
TEST_DATA_LABEL = 'Test Data'
RED_SEA_ORIGIN = 'Red Sea'

TEST_MARKER = "[TEST DATA]"


def decimal_value(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


AMBER_VARIANTS = [
    ("عسلي فاخر", "Premium Honey", "Baltic", "عسلي", BARREL_SHAPE_AR, "كركوشة حرير فاخرة"),
    ("أحمر معتّق", "Aged Deep Red", "Baltic", "أحمر داكن", OVAL_SHAPE_AR, CLASSIC_TASSEL_AR),
    ("ليموني صافي", "Clear Lemon", "Baltic", "ليموني", ROUND_SHAPE_AR, SILK_TASSEL_AR),
    ("كرزي داكن", "Dark Cherry", "Baltic", "كرزي داكن", BARREL_SHAPE_AR, LUXURY_TASSEL_AR),
    ("كونياك كلاسيكي", "Classic Cognac", "Baltic", "كونياك", OVAL_SHAPE_AR, SILK_TASSEL_AR),
    ("ذهبي شفاف", "Transparent Golden", "Baltic", "ذهبي", ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    ("عسلي معتّق", "Aged Honey", "Baltic", "عسلي معتّق", BARREL_SHAPE_AR, CLASSIC_TASSEL_AR),
    ("أصفر دافئ", "Warm Yellow", "Baltic", "أصفر دافئ", OVAL_SHAPE_AR, SILK_TASSEL_AR),
    ("بني محمر", "Reddish Brown", "Baltic", "بني محمر", BARREL_SHAPE_AR, LUXURY_TASSEL_AR),
    ("برتقالي غني", "Rich Orange", "Baltic", "برتقالي", ROUND_SHAPE_AR, SILK_TASSEL_AR),
    ("عسلي فاتح", "Light Honey", "Baltic", "عسلي فاتح", OVAL_SHAPE_AR, CLASSIC_TASSEL_AR),
    ("كرزي معتّق", "Aged Cherry", "Baltic", "كرزي", BARREL_SHAPE_AR, LUXURY_TASSEL_AR),
    ("ذهبي معتّق", "Aged Golden", "Baltic", "ذهبي معتّق", ROUND_SHAPE_AR, SILK_TASSEL_AR),
    ("ليموني معتّق", "Aged Lemon", "Baltic", "ليموني معتّق", OVAL_SHAPE_AR, CLASSIC_TASSEL_AR),
    ("عسلي داكن", "Dark Honey", "Baltic", "عسلي داكن", BARREL_SHAPE_AR, LUXURY_TASSEL_AR),
    ("كونياك فاتح", "Light Cognac", "Baltic", "كونياك فاتح", ROUND_SHAPE_AR, SILK_TASSEL_AR),
    ("أحمر كلاسيكي", "Classic Red", "Baltic", "أحمر", OVAL_SHAPE_AR, LUXURY_TASSEL_AR),
    ("بني ذهبي", "Golden Brown", "Baltic", "بني ذهبي", BARREL_SHAPE_AR, CLASSIC_TASSEL_AR),
    ("برتقالي فاتح", "Light Orange", "Baltic", "برتقالي فاتح", ROUND_SHAPE_AR, SILK_TASSEL_AR),
    ("عسلي ملكي", "Royal Honey", "Baltic", "عسلي ملكي", OVAL_SHAPE_AR, LUXURY_TASSEL_AR),
    ("كرزي فاخر", "Premium Cherry", "Baltic", "كرزي فاخر", BARREL_SHAPE_AR, SILK_TASSEL_AR),
    ("ذهبي فاخر", "Premium Golden", "Baltic", "ذهبي فاخر", ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    (
        "كونياك داكن",
        "Dark Cognac",
        "Baltic",
        "كونياك داكن",
        OVAL_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
    ("ليموني فاخر", "Premium Lemon", "Baltic", "ليموني فاخر", BARREL_SHAPE_AR, SILK_TASSEL_AR),
    ("أحمر ذهبي", "Golden Red", "Baltic", "أحمر ذهبي", ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    (
        "عسلي كلاسيكي",
        "Classic Honey",
        "Baltic",
        "عسلي كلاسيكي",
        OVAL_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
    ("كرزي شفاف", "Transparent Cherry", "Baltic", "كرزي شفاف", BARREL_SHAPE_AR, SILK_TASSEL_AR),
    ("ذهبي فاتح", "Light Golden", "Baltic", "ذهبي فاتح", ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    ("كونياك فاخر", "Premium Cognac", "Baltic", "كونياك فاخر", OVAL_SHAPE_AR, SILK_TASSEL_AR),
    ("عسلي أحمر", "Red Honey", "Baltic", "عسلي محمر", BARREL_SHAPE_AR, LUXURY_TASSEL_AR),
]

MAMMOTH_VARIANTS = [
    ("كريمي كلاسيكي", "Classic Cream", "Siberia", "كريمي", ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    (
        AGED_IVORY_AR,
        "Aged Ivory Tone",
        "Siberia",
        AGED_IVORY_AR,
        OVAL_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
    ("كريمي مخطط", "Grained Cream", "Siberia", "كريمي مخطط", BARREL_SHAPE_AR, SILK_TASSEL_AR),
    (LIGHT_IVORY_AR, "Light Ivory Tone", "Siberia", LIGHT_IVORY_AR, ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    (
        WARM_IVORY_AR,
        "Warm Ivory Tone",
        "Siberia",
        WARM_IVORY_AR,
        OVAL_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
    ("كريمي داكن", "Deep Cream", "Siberia", "كريمي داكن", BARREL_SHAPE_AR, SILK_TASSEL_AR),
    ("عاجي كلاسيكي", "Classic Ivory Tone", "Siberia", "عاجي", ROUND_SHAPE_AR, LUXURY_TASSEL_AR),
    ("كريمي فاخر", "Premium Cream", "Siberia", "كريمي فاخر", OVAL_SHAPE_AR, SILK_TASSEL_AR),
]

ELEPHANT_VARIANTS = [
    (
        "عاجي فاتح تجريبي",
        "Light Ivory Test",
        TEST_DATA_LABEL,
        LIGHT_IVORY_AR,
        ROUND_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
    (
        "عاجي دافئ تجريبي",
        "Warm Ivory Test",
        TEST_DATA_LABEL,
        WARM_IVORY_AR,
        OVAL_SHAPE_AR,
        SILK_TASSEL_AR,
    ),
    (
        "عاجي كلاسيكي تجريبي",
        "Classic Ivory Test",
        TEST_DATA_LABEL,
        "عاجي",
        BARREL_SHAPE_AR,
        LUXURY_TASSEL_AR,
    ),
    (
        "عاجي معتّق تجريبي",
        "Aged Ivory Test",
        TEST_DATA_LABEL,
        AGED_IVORY_AR,
        ROUND_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
]

YUSR_VARIANTS = [
    (
        "يسر أسود كلاسيكي",
        "Classic Black Yusr",
        RED_SEA_ORIGIN,
        "أسود",
        ROUND_SHAPE_AR,
        "كركوشة فضية",
    ),
    (
        "يسر أسود مطعّم",
        "Inlaid Black Yusr",
        RED_SEA_ORIGIN,
        "أسود مطعّم",
        OVAL_SHAPE_AR,
        LUXURY_TASSEL_AR,
    ),
    ("يسر بني داكن", "Dark Brown Yusr", RED_SEA_ORIGIN, "بني داكن", BARREL_SHAPE_AR, SILK_TASSEL_AR),
    (
        "يسر أسود فاخر",
        "Premium Black Yusr",
        RED_SEA_ORIGIN,
        "أسود لامع",
        ROUND_SHAPE_AR,
        LUXURY_TASSEL_AR,
    ),
    (
        "يسر مطعّم كلاسيكي",
        "Classic Inlaid Yusr",
        RED_SEA_ORIGIN,
        "أسود وفضي",
        OVAL_SHAPE_AR,
        "كركوشة فضية",
    ),
    (
        "يسر أسود معتّق",
        "Aged Black Yusr",
        RED_SEA_ORIGIN,
        "أسود معتّق",
        BARREL_SHAPE_AR,
        CLASSIC_TASSEL_AR,
    ),
    (
        "يسر فاخر مطعّم",
        "Premium Inlaid Yusr",
        RED_SEA_ORIGIN,
        "أسود مطعّم",
        ROUND_SHAPE_AR,
        LUXURY_TASSEL_AR,
    ),
    (
        "يسر كلاسيكي ثقيل",
        "Heavy Classic Yusr",
        RED_SEA_ORIGIN,
        "أسود داكن",
        OVAL_SHAPE_AR,
        SILK_TASSEL_AR,
    ),
]


def build_specs():
    specs = []

    for i, (ar_variant, en_variant, origin, color, shape, tassel) in enumerate(
        AMBER_VARIANTS, start=1
    ):
        selling = decimal_value(2450 + (i * 115))
        cost = decimal_value(selling * decimal_value("0.56"))
        discount = decimal_value(selling - decimal_value(180 + (i % 4) * 40)) if i % 3 == 0 else None
        bead_count = 33 if i % 6 else 45
        specs.append(
            {
                "material_key": "amber",
                "name_ar": f"مسباح كهرمان طبيعي حر {ar_variant}",
                "name_en": f"Natural Free Amber Misbah – {en_variant}",
                "origin": origin,
                "color": color,
                "bead_count": bead_count,
                "bead_size_mm": decimal_value(10.40 + (i % 8) * 0.45),
                "weight_g": decimal_value(30.80 + i * 0.62),
                "shape": shape,
                "tassel_type": tassel,
                "condition": "جديد - بيانات تجريبية",
                "cost_price": cost,
                "selling_price": selling,
                "discount_price": discount,
                "is_featured": i in {1, 4, 10, 20, 24},
                "is_new_arrival": i in {1, 2, 5, 11, 17, 23, 29},
                "is_best_seller": i in {3, 7, 14, 21, 27},
                "verification_status": Product.VerificationStatus.INSPECTED
                if i % 4
                else Product.VerificationStatus.NONE,
            }
        )

    for i, (ar_variant, en_variant, origin, color, shape, tassel) in enumerate(
        MAMMOTH_VARIANTS, start=1
    ):
        selling = decimal_value(4650 + i * 270)
        specs.append(
            {
                "material_key": "mammoth",
                "name_ar": f"مسباح عاج ماموث {ar_variant}",
                "name_en": f"Mammoth Ivory Misbah – {en_variant}",
                "origin": origin,
                "color": color,
                "bead_count": 33,
                "bead_size_mm": decimal_value(10.80 + i * 0.35),
                "weight_g": decimal_value(46.00 + i * 1.75),
                "shape": shape,
                "tassel_type": tassel,
                "condition": "ممتاز - بيانات تجريبية",
                "cost_price": decimal_value(selling * decimal_value("0.57")),
                "selling_price": selling,
                "discount_price": decimal_value(selling - 350) if i in {2, 6} else None,
                "is_featured": i in {1, 5},
                "is_new_arrival": i in {3, 7},
                "is_best_seller": i in {2, 8},
                "verification_status": Product.VerificationStatus.INSPECTED,
            }
        )

    for i, (ar_variant, en_variant, origin, color, shape, tassel) in enumerate(
        ELEPHANT_VARIANTS, start=1
    ):
        selling = decimal_value(6100 + i * 310)
        specs.append(
            {
                "material_key": "elephant",
                "name_ar": f"مسباح عاج فيل {ar_variant}",
                "name_en": f"Elephant Ivory Misbah – {en_variant}",
                "origin": origin,
                "color": color,
                "bead_count": 33,
                "bead_size_mm": decimal_value(11.20 + i * 0.30),
                "weight_g": decimal_value(50.50 + i * 2.10),
                "shape": shape,
                "tassel_type": tassel,
                "condition": "بيانات اختبار فقط - غير مخصص للبيع",
                "cost_price": decimal_value(selling * decimal_value("0.55")),
                "selling_price": selling,
                "discount_price": None,
                "is_featured": False,
                "is_new_arrival": False,
                "is_best_seller": False,
                "verification_status": Product.VerificationStatus.NONE,
            }
        )

    for i, (ar_variant, en_variant, origin, color, shape, tassel) in enumerate(
        YUSR_VARIANTS, start=1
    ):
        selling = decimal_value(1250 + i * 165)
        specs.append(
            {
                "material_key": "yusr",
                "name_ar": f"مسباح {ar_variant}",
                "name_en": f"{en_variant} Misbah",
                "origin": origin,
                "color": color,
                "bead_count": 33 if i not in {4, 8} else 45,
                "bead_size_mm": decimal_value(9.80 + i * 0.40),
                "weight_g": decimal_value(24.50 + i * 1.35),
                "shape": shape,
                "tassel_type": tassel,
                "condition": "جديد - بيانات تجريبية",
                "cost_price": decimal_value(selling * decimal_value("0.54")),
                "selling_price": selling,
                "discount_price": decimal_value(selling - 150) if i in {3, 7} else None,
                "is_featured": i in {2, 7},
                "is_new_arrival": i in {1, 5},
                "is_best_seller": i in {4, 8},
                "verification_status": Product.VerificationStatus.INSPECTED
                if i % 2
                else Product.VerificationStatus.NONE,
            }
        )

    if len(specs) != 50:
        raise RuntimeError(f"Expected 50 demo products, built {len(specs)}.")
    return specs


def _descriptions(spec):
    material_ar = {
        "amber": "الكهرمان الطبيعي الحر",
        "mammoth": "عاج الماموث",
        "elephant": "عاج الفيل",
        "yusr": "اليسر",
    }[spec["material_key"]]
    material_en = {
        "amber": "natural free amber",
        "mammoth": "mammoth ivory",
        "elephant": "elephant ivory",
        "yusr": "yusr",
    }[spec["material_key"]]

    legal_ar = (
        " هذا سجل تجريبي فقط وغير مخصص للبيع الفعلي."
        if spec["material_key"] == "elephant"
        else " البيانات مخصصة لاختبار المتجر فقط."
    )
    legal_en = (
        " This is test-only data and is not intended for actual sale."
        if spec["material_key"] == "elephant"
        else " The data is intended only for store testing."
    )

    ar = (
        f"{TEST_MARKER} {spec['name_ar']} من {material_ar}، بعدد {spec['bead_count']} حبة، "
        f"بلون {spec['color']} وشكل {spec['shape']}. وزن القطعة التجريبي {spec['weight_g']} جم "
        f"ومتوسط مقاس الحبة {spec['bead_size_mm']} مم، مع {spec['tassel_type']}."
        f"{legal_ar}"
    )
    en = (
        f"{TEST_MARKER} {spec['name_en']} in {material_en}, featuring {spec['bead_count']} beads, "
        f"{spec['color']} color and {spec['shape']} shape. Demo weight is {spec['weight_g']} g with an "
        f"average bead size of {spec['bead_size_mm']} mm and {spec['tassel_type']}."
        f"{legal_en}"
    )
    return ar, en


def _test_image(product, image_no):
    # Deliberately obvious placeholder: never represents a real product or provenance.
    size = (1200, 1200)
    backgrounds = [(245, 240, 228), (235, 235, 235), (229, 239, 242)]
    image = Image.new("RGB", size, backgrounds[(image_no - 1) % len(backgrounds)])
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 1120, 1120), outline=(60, 60, 60), width=8)
    draw.text((130, 165), "HAYBAT ALSULTAN", fill=(20, 20, 20))
    draw.text((130, 255), "TEST PRODUCT IMAGE", fill=(20, 20, 20))
    draw.text((130, 350), f"SKU: {product.sku}", fill=(20, 20, 20))
    draw.text((130, 430), f"VIEW: {image_no} OF 3", fill=(20, 20, 20))
    draw.text((130, 520), "NOT A REAL PRODUCT PHOTO", fill=(20, 20, 20))
    draw.text((130, 610), product.name_en[:70], fill=(20, 20, 20))

    output = BytesIO()
    image.save(output, format="JPEG", quality=90, optimize=True)
    payload = output.getvalue()
    return SimpleUploadedFile(
        f"{product.sku.lower()}-test-{image_no}.jpg",
        payload,
        content_type="image/jpeg",
    )


class Command(BaseCommand):
    help = "Create/update 50 idempotent demo products for local pre-Render testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-images",
            action="store_true",
            help="Generate and upload 3 clearly-marked TEST images per product using the existing Cloudinary service.",
        )

    @transaction.atomic
    def _ensure_master_data(self):
        category, _ = Category.objects.get_or_create(
            name_en="Misbah",
            defaults={"name_ar": "المسابيح", "sort_order": 10, "is_active": True},
        )
        materials = {}
        definitions = {
            "amber": ("كهرمان طبيعي حر", "Natural Free Amber", 10),
            "mammoth": ("عاج ماموث", "Mammoth Ivory", 20),
            "elephant": ("عاج فيل - تجريبي فقط", "Elephant Ivory - Test Only", 30),
            "yusr": ("يسر", "Yusr", 40),
        }
        for key, (name_ar, name_en, sort_order) in definitions.items():
            material, _ = Material.objects.get_or_create(
                name_en=name_en,
                defaults={
                    "name_ar": name_ar,
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )
            materials[key] = material
        return category, materials

    def _upsert_product(self, spec, category, materials):
        description_ar, description_en = _descriptions(spec)
        meta_title_ar = f"{spec['name_ar']} | هيبة السلطان"[:180]
        meta_title_en = f"{spec['name_en']} | Haybat Alsultan"[:180]
        meta_description_ar = (
            f"{TEST_MARKER} {spec['name_ar']}، {spec['bead_count']} حبة، لون {spec['color']}، "
            f"وزن {spec['weight_g']} جم. بيانات تجريبية لاختبار متجر هيبة السلطان."
        )[:320]
        meta_description_en = (
            f"{TEST_MARKER} {spec['name_en']}, {spec['bead_count']} beads, {spec['color']}, "
            f"{spec['weight_g']} g. Demo data for Haybat Alsultan storefront testing."
        )[:320]

        defaults = {
            "name_en": spec["name_en"],
            "description_ar": description_ar,
            "description_en": description_en,
            "meta_title_ar": meta_title_ar,
            "meta_title_en": meta_title_en,
            "meta_description_ar": meta_description_ar,
            "meta_description_en": meta_description_en,
            "category": category,
            "material": materials[spec["material_key"]],
            "origin": spec["origin"],
            "color": spec["color"],
            "bead_count": spec["bead_count"],
            "bead_size_mm": spec["bead_size_mm"],
            "weight_g": spec["weight_g"],
            "shape": spec["shape"],
            "tassel_type": spec["tassel_type"],
            "condition": spec["condition"],
            "cost_price": spec["cost_price"],
            "selling_price": spec["selling_price"],
            "discount_price": spec["discount_price"],
            "available_quantity": 1,
            "reserved_quantity": 0,
            "status": Product.Status.AVAILABLE,
            "is_featured": spec["is_featured"],
            "is_new_arrival": spec["is_new_arrival"],
            "is_best_seller": spec["is_best_seller"],
            "verification_status": spec["verification_status"],
        }

        product = Product.objects.filter(
            name_ar=spec["name_ar"], description_ar__startswith=TEST_MARKER
        ).first()
        created = product is None
        if created:
            product = Product(name_ar=spec["name_ar"], **defaults)
        else:
            for field, value in defaults.items():
                setattr(product, field, value)

        if (
            product.discount_price is not None
            and product.discount_price > product.selling_price
        ):
            raise CommandError(f"Invalid demo discount for {product.name_ar}.")
        product.full_clean(exclude=["product_reference", "sku"])
        product.save()
        return product, created

    def _ensure_images(self, product):
        existing_count = product.images.count()
        if existing_count >= 3:
            return 0

        uploads = [
            _test_image(product, image_no) for image_no in range(existing_count + 1, 4)
        ]
        created = attach_product_images(product, uploads)
        for image_no, image in enumerate(
            product.images.order_by("sort_order", "id"), start=1
        ):
            update_image_metadata(
                image,
                alt_text_ar=f"صورة اختبارية {image_no} من 3 — {product.name_ar}",
                alt_text_en=f"Test image {image_no} of 3 — {product.name_en}",
                sort_order=image_no,
            )
        return len(created)

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        products = []

        # Product/master-data creation is all-or-nothing. Cloudinary uploads are
        # intentionally performed afterwards because they are external side effects.
        with transaction.atomic():
            category, materials = self._ensure_master_data()
            for spec in build_specs():
                product, created = self._upsert_product(spec, category, materials)
                products.append(product)
                created_count += int(created)
                updated_count += int(not created)

        image_count = 0
        if options["with_images"]:
            self.stdout.write(
                "Uploading generated TEST images through the existing Cloudinary service..."
            )
            for product in products:
                try:
                    image_count += self._ensure_images(product)
                except Exception as exc:
                    raise CommandError(
                        f"Image upload failed for {product.sku}. Products remain safe and the command can be rerun. Error: {exc}"
                    ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo seed complete: {created_count} created, {updated_count} updated, "
                f"{image_count} images uploaded. Total demo products: {len(products)}."
            )
        )
        if not options["with_images"]:
            self.stdout.write(
                "No images uploaded. Re-run with --with-images after Cloudinary is configured."
            )
