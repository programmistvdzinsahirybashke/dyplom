from django.http import JsonResponse
from django.template.loader import render_to_string
from carts.utils import get_user_carts
from goods.models import Service
from carts.models import Cart


# Create your views here.

# Представление для добавления услуги в корзину.
# Получает ID услуги из POST-запроса и либо увеличивает количество,
# либо создаёт новую запись в корзине (в зависимости от авторизации пользователя).
def cart_add(request):
    product_id = request.POST.get("product_id")
    product = Service.objects.get(id=product_id)

    if request.user.is_authenticated:
        carts = Cart.objects.filter(user=request.user, product=product)
        if carts.exists():
            cart = carts.first()
            if cart:
                cart.quantity += 1
                cart.save()
        else:
            Cart.objects.create(user=request.user, product=product, quantity=1)

    else:
        carts = Cart.objects.filter(
            session_key=request.session.session_key, product=product)
        if carts.exists():
            cart = carts.first()
            if cart:
                cart.quantity += 1
                cart.save()
        else:
            Cart.objects.create(
                session_key=request.session.session_key, product=product, quantity=1)

    user_cart = get_user_carts(request)
    cart_items_html = render_to_string(
        "carts/includes/included_cart.html", {"carts": user_cart}, request=request)
    response_data = {
        "message": "Товар добавлен в корзину",
        "cart_items_html": cart_items_html,
    }
    return JsonResponse(response_data)

# Представление для изменения количества услуги в корзине.
# Получает ID позиции и новое количество из POST-запроса, обновляет значение
# и возвращает обновлённую HTML-разметку корзины.
def cart_change(request):
    cart_id = request.POST.get("cart_id")
    quantity = request.POST.get("quantity")

    cart = Cart.objects.get(id=cart_id)

    cart.quantity = quantity
    cart.save()
    updated_quantity = cart.quantity

    cart = get_user_carts(request)
    cart_items_html = render_to_string(
        "carts/includes/included_cart.html", {"carts": cart}, request=request)

    response_data = {
        "message": "Количество изменено",
        "cart_items_html": cart_items_html,
        "quantity": updated_quantity,
    }

    return JsonResponse(response_data)

# Представление для удаления услуги из корзины.
# Получает ID позиции из POST-запроса, удаляет её из корзины
# и возвращает HTML корзины без удалённого элемента.
def cart_remove(request):
    cart_id = request.POST.get("cart_id")

    cart = Cart.objects.get(id=cart_id)
    quantity = cart.quantity
    cart.delete()

    user_cart = get_user_carts(request)
    cart_items_html = render_to_string(
        "carts/includes/included_cart.html", {"carts": user_cart}, request=request)

    response_data = {
        "message": "Товар удален",
        "cart_items_html": cart_items_html,
        "quantity_deleted": quantity,
    }

    return JsonResponse(response_data)
