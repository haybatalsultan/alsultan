from orders.models import Expense

_CATEGORY_LABELS = {
    Expense.Category.BOXES: {"ar": "صناديق", "en": "Boxes"},
    Expense.Category.BAGS: {"ar": "أكياس", "en": "Bags"},
    Expense.Category.PACKAGING: {"ar": "مواد التغليف", "en": "Packaging materials"},
    Expense.Category.CARDS_LABELS: {"ar": "بطاقات وملصقات", "en": "Cards & labels"},
    Expense.Category.SHIPPING_DELIVERY: {
        "ar": "الشحن والتوصيل",
        "en": "Shipping & delivery",
    },
    Expense.Category.MARKETING: {"ar": "التسويق", "en": "Marketing"},
    Expense.Category.SUBSCRIPTIONS: {
        "ar": "الاشتراكات والخدمات",
        "en": "Subscriptions & services",
    },
    Expense.Category.PAYMENT_FEES: {"ar": "رسوم الدفع", "en": "Payment fees"},
    Expense.Category.OFFICE: {"ar": "المكتب والتشغيل", "en": "Office & operations"},
    Expense.Category.OTHER: {"ar": "أخرى", "en": "Other"},
}

_STATUS_LABELS = {
    Expense.Status.ACTIVE: {"ar": "نشط", "en": "Active"},
    Expense.Status.VOIDED: {"ar": "ملغى", "en": "Voided"},
}


def _language(language_code: str | None) -> str:
    return "en" if str(language_code or "ar").lower().startswith("en") else "ar"


def category_label(value: str, language_code: str | None = "ar") -> str:
    labels = _CATEGORY_LABELS.get(value)
    if not labels:
        return value
    return labels[_language(language_code)]


def status_label(value: str, language_code: str | None = "ar") -> str:
    labels = _STATUS_LABELS.get(value)
    if not labels:
        return value
    return labels[_language(language_code)]


def category_choices(language_code: str | None = "ar") -> list[tuple[str, str]]:
    return [
        (value, category_label(value, language_code))
        for value, _ in Expense.Category.choices
    ]
