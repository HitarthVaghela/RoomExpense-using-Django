from django import template

register = template.Library()

@register.filter
def absval(value):
    return abs(value) 