from django.shortcuts import render
from goods.models import Service
from django.core.paginator import Paginator
from goods.utils import q_search


# Create your views here.

# Представление для отображения каталога товаров (услуг).
# Поддерживает фильтрацию по категории, поиск по ключевым словам,
# фильтрацию по скидке и сортировку, а также постраничный вывод.
def catalog(request, category_slug=None):
    page = request.GET.get('page', 1)
    on_sale = request.GET.get('on_sale', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)

    if category_slug == "all":
        goods = Service.objects.all()
    elif query:
        goods = q_search(query)
    else:
        goods = Service.objects.filter(category__slug=category_slug)

    if on_sale:
        goods = goods.filter(discount__gt=0)

    if order_by and order_by != "default":
        goods = goods.order_by(order_by)

    paginator = Paginator(goods, 6)
    current_page = paginator.page(int(page))

    context = {
        "title": "RepAir - Каталог",
        "goods": current_page,
        "slug_url": category_slug
    }
    return render(request, "goods/catalog.html", context)

# Представление для отображения страницы конкретного товара (услуги).
# Получает товар по его slug и передаёт его в шаблон для отображения.
def product(request, product_slug):
    product = Service.objects.get(slug=product_slug)

    context = {
        'product': product
    }

    return render(request, 'goods/product.html', context=context)
