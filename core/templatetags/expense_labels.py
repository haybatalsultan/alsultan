from django import template

from orders.services.expense_labels import category_label, status_label

register = template.Library()


@register.simple_tag(takes_context=True)
def expense_category_label(context, value):
    request = context.get("request")
    language_code = getattr(
        request, "LANGUAGE_CODE", context.get("LANGUAGE_CODE", "ar")
    )
    return category_label(value, language_code)


@register.simple_tag(takes_context=True)
def expense_status_label(context, value):
    request = context.get("request")
    language_code = getattr(
        request, "LANGUAGE_CODE", context.get("LANGUAGE_CODE", "ar")
    )
    return status_label(value, language_code)
