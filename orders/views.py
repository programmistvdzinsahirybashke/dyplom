from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import redirect, render
from carts.models import Cart
from orders.forms import CreateOrderForm
from orders.models import Order, OrderItem
from datetime import datetime


# Create your views here.
@login_required
def create_order(request):
    if request.method == 'POST':
        form = CreateOrderForm(data=request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = request.user
                    cart_items = Cart.objects.filter(user=user)
                    if cart_items.exists():
                        # Извлекаем дату и время из формы
                        delivery_date = form.cleaned_data['delivery_date']
                        delivery_time = form.cleaned_data['delivery_time']
                        print(delivery_time)

                        # Проверка на правильность формата времени
                        # Преобразуем строку времени в объект времени
                        if isinstance(delivery_time, str):
                            delivery_time = datetime.strptime(delivery_time, '%H:%M').time()

                        # Создать заказ
                        order = Order.objects.create(
                            user=user,
                            phone_number=form.cleaned_data['phone_number'],
                            requires_delivery=form.cleaned_data['requires_delivery'],
                            delivery_address=form.cleaned_data['delivery_address'],
                            delivery_date=delivery_date,  # Сохраняем дату доставки
                            delivery_time=delivery_time,    # Сохраняем время доставки
                            payment_on_get=form.cleaned_data['payment_on_get'],
                            comment = form.cleaned_data['comment']
                        )
                        # Создать заказанные товары
                        for cart_item in cart_items:
                            product = cart_item.product
                            name = cart_item.product.service_name
                            price = cart_item.product.sell_price()
                            quantity = cart_item.quantity

                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                name=name,
                                price=price,
                                quantity=quantity,
                            )

                            product.save()

                        # Очистить корзину пользователя после создания заказа
                        cart_items.delete()
                        messages.success(request, 'Заказ оформлен!')
                        return redirect('user:profile')
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('cart:order')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
        form = CreateOrderForm(initial=initial)

    context = {
        'title': 'RepAir - Оформление заказа',
        'form': form,
        'order':True,
    }
    return render(request, 'orders/create_order.html', context=context)


from django.http import JsonResponse
from .models import Order
from datetime import datetime


def get_occupied_times(request):
    # Получаем параметр "date" из GET-запроса
    date = request.GET.get('date')

    # Если дата не указана или недопустима, возвращаем пустой список
    if not date:
        return JsonResponse({'occupied_times': []})

    # Преобразуем строку даты в объект Date
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'occupied_times': []})

    # Извлекаем все заказы для указанной даты, которые имеют время доставки
    orders = Order.objects.filter(delivery_date=date_obj).values_list('delivery_time', flat=True)

    # Преобразуем занятые интервалы в формат HH:MM
    occupied_times = [time.strftime('%H:%M') for time in orders]

    return JsonResponse({'occupied_times': occupied_times})