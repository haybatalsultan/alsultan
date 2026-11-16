import json

from django import template

register = template.Library()


@register.filter
def json_pretty(value):
    try:
        return json.dumps(
            value or {}, ensure_ascii=False, indent=2, sort_keys=True, default=str
        )
    except (TypeError, ValueError):
        return "{}"
