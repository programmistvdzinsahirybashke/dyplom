from django import template

from orders.models import Status

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)


# Фильтр для поиска статуса по имени
@register.filter
def filter_by_name(queryset, name):
    return queryset.filter(status_name=name)
