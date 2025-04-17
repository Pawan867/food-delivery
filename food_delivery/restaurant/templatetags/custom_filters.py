from django import template

register = template.Library()


@register.filter
def to_range(value):
    try:
        return range(int(value))
    except:
        return []


@register.filter
def remaining_stars(rating):
    try:
        return range(5 - int(rating))
    except:
        return []
