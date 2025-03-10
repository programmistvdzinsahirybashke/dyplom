from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from django.db.models import Prefetch, Sum, F
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q

from carts.models import Cart
from goods.models import Category
from users.forms import UserLoginForm, UserRegistrationForm, ProfileForm

from orders.models import Order, OrderItem, Status


# Create your views here.
def login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)

            session_key = request.session.session_key

            if user:
                auth.login(request, user)
                messages.success(request, f'{username}, Вы вошли в аккаунт')

                if session_key:
                    Cart.objects.filter(session_key=session_key).update(user=user)

                redirect_page = request.POST.get('next', None)
                if redirect_page and redirect_page != reverse('user:logout'):
                    return HttpResponseRedirect(request.POST.get('next'))

                return HttpResponseRedirect(reverse('repair_app:index'))
    else:
        form = UserLoginForm()

    context = {
        'title': 'Вход',
        'form': form,
    }
    return render(request, 'users/login.html', context=context)


def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()

            session_key = request.session.session_key

            user = form.instance
            auth.login(request, user)

            if session_key:
                Cart.objects.filter(session_key=session_key).update(user=user)

            messages.success(request, f'{user.username}, Вы зарегистрированы и вошли в аккаунт')

            return HttpResponseRedirect(reverse('repair_app:index'))
    else:
        form = UserRegistrationForm()

    context = {
        'title': 'Регистрация',
        'form': form,
    }
    return render(request, 'users/registration.html', context=context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f'Профиль обновлен')
            return HttpResponseRedirect(reverse('user:profile'))
    else:
        form = ProfileForm(instance=request.user)

    orders = Order.objects.filter(user=request.user).prefetch_related(
        Prefetch(
            "orderitem_set",
            queryset=OrderItem.objects.select_related("product"),
        )
    ).order_by("-id")

    # Вычисляем общую сумму для каждого заказа
    for order in orders:
        order.total = order.orderitem_set.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0

    context = {
        'title': 'Мой профиль',
        'form': form,
        'orders': orders,
    }
    return render(request, 'users/profile.html', context=context)


def users_cart(request):
    return render(request, 'users/users_cart.html')


@login_required
def logout(request):
    messages.success(request, f'Вы вышли из аккаунта')
    auth.logout(request)
    return redirect(reverse('repair_app:index'))


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from orders.models import Order, OrderItem
from orders.models import Order, OrderItem, Status, Employee  # Убедитесь, что Employee импортирован
from django.http import QueryDict


@login_required
def admin_orders(request):
    if not request.user.is_superuser:
        raise Http404("Доступ ограничен: только для администраторов.")

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_order = request.GET.get('sort', 'desc')

    # Получаем заказы с фильтрацией
    orders = Order.objects.all()
    statuses = Status.objects.filter(status_category='Заказ')

    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    if status_filter:
        orders = orders.filter(status__id=status_filter)

    orders = orders.order_by('-id' if sort_order == 'desc' else 'id')

    # Собираем доступных сотрудников для каждой услуги
    available_employees = {}
    employee_statuses = {}

    for order in orders:
        for item in order.orderitem_set.all():
            item_category = item.product.category
            employees = Employee.objects.filter(category=item_category)
            available_employees[item.id] = employees

            # Собираем информацию о заявках в статусе "В работе" для каждого сотрудника
            for employee in employees:
                in_progress_count = OrderItem.objects.filter(employee=employee, status__status_name="В работе").count()
                employee_statuses[employee.id] = in_progress_count

    if request.method == 'POST':
        # Обработка назначения сотрудника на одну услугу
        if 'assign_single' in request.POST:
            order_item_id = request.POST.get('order_item_id')
            employee_id = request.POST.get('employee_id')
            try:
                order_item = OrderItem.objects.get(id=order_item_id)
                employee = Employee.objects.get(id=employee_id)
                order_item.employee = employee
                order_item.save()
            except (OrderItem.DoesNotExist, Employee.DoesNotExist):
                pass

        # Обработка назначения сотрудников на все услуги
        elif 'assign_all' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id)

                # Обрабатываем сотрудников для каждой услуги
                for item in order.orderitem_set.all():
                    employee_id = request.POST.get(f'employee_{item.id}')
                    if employee_id:
                        try:
                            employee = Employee.objects.get(id=employee_id)
                            if employee.category == item.product.category:  # Проверяем соответствие категории
                                item.employee = employee
                                item.save()
                        except Employee.DoesNotExist:
                            pass
            except Order.DoesNotExist:
                pass

            messages.success(request, f'Сотрудники назначены (заказ №{order_id})')
            query_params = QueryDict(mutable=True)
            query_params['search'] = search_query
            query_params['status'] = status_filter
            query_params['sort'] = sort_order
            redirect_url = f"{request.path}?{query_params.urlencode()}"
            return HttpResponseRedirect(redirect_url)

        elif 'update_order' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id)

                # Обновляем поля заказа
                status_id = request.POST.get('status')
                requires_delivery = request.POST.get('requires_delivery')
                delivery_address = request.POST.get('delivery_address')
                comment = request.POST.get('comment')

                # Обновление статуса
                if status_id:
                    order.status_id = status_id

                # Обновление адреса доставки
                if delivery_address:
                    order.delivery_address = delivery_address

                # Обновление комментария
                if comment:
                    order.comment = comment

                order.save()  # Сохраняем изменения
                messages.success(request, f'Данные обновлены и сохранены (заказ №{order_id})')
                query_params = QueryDict(mutable=True)
                query_params['search'] = search_query
                query_params['status'] = status_filter
                query_params['sort'] = sort_order
                redirect_url = f"{request.path}?{query_params.urlencode()}"
                return HttpResponseRedirect(redirect_url)

            except Order.DoesNotExist:
                pass


    context = {
        'title': 'Все заказы',
        'orders': orders,
        'statuses': statuses,
        'available_employees': available_employees,
        'employee_statuses': employee_statuses,
        'filters': {
            'search_query': search_query,
            'status_filter': status_filter,
            'sort_order': sort_order,
        },
    }

    return render(request, 'users/admin_orders.html', context)


from django.http import HttpResponseRedirect


def update_employee(request, order_id):
    order = Order.objects.get(id=order_id)
    employee_id = request.POST.get('employee')
    if employee_id:
        employee = Employee.objects.get(id=employee_id)
        # Обновляем сотрудника в заказе
        orderitem = OrderItem.objects.get(order=order)
        orderitem.employee = employee
        orderitem.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404
from django.db.models import Q


@login_required
def staff_orders(request):
    if not request.user.is_staff:
        raise Http404("Доступ ограничен: только для сотрудников.")
    current_user = request.user.id
    current_employee = Employee.objects.get(user_id=current_user)

    # Фильтры
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_order = request.GET.get('sort', 'desc')

    # Фильтруем заявки, назначенные текущему сотруднику
    order_items = OrderItem.objects.filter(employee=current_employee)

    # Применяем фильтрацию по поисковому запросу
    if search_query:
        order_items = order_items.filter(
            Q(order__id__icontains=search_query) |
            Q(order__user__username__icontains=search_query)
        )

    # Применяем фильтрацию по статусу
    if status_filter:
        order_items = order_items.filter(status__id=status_filter)

    # Получаем уникальные заказы, связанные с отфильтрованными заявками
    orders = Order.objects.filter(orderitem__in=order_items).distinct()

    # Применяем сортировку
    if sort_order == 'asc':
        orders = orders.order_by('id')
    else:
        orders = orders.order_by('-id')

    # Получаем все доступные статусы
    statuses = Status.objects.filter(status_category='Услуга')

    # Обработка изменения статуса услуги
    if request.method == 'POST':
        order_item_id = request.POST.get('order_item_id')
        new_status_name = request.POST.get('new_status')


        if order_item_id and new_status_name:
            try:
                order_id = request.POST.get('order_id')
                # Получаем заявку, для которой нужно изменить статус
                order_item = OrderItem.objects.get(id=order_item_id, employee=current_employee)

                # Получаем новый статус по имени
                new_status = Status.objects.get(status_name=new_status_name)

                # Обновляем статус заявки
                order_item.status = new_status

                # Если статус "В работе", сбрасываем дату выполнения
                if new_status.status_name == "В работе":
                    order_item.work_ended_datetime = None
                    messages.success(request, f'Отменено выполнение задачи (Заказ №{order_id} заявка №{order_item_id})')

                if new_status.status_name == "Выполнено":

                    messages.success(request, f'Задача выполнена(Заказ №{order_id} заявка №{order_item_id})')

                # Сохраняем изменения
                order_item.save()


                # Перенаправляем с сохранением параметров
                redirect_url = f"{request.path}?search={search_query}&status={status_filter}&sort={sort_order}"
                return HttpResponseRedirect(redirect_url)
            except OrderItem.DoesNotExist:
                pass  # Если заказ или заявка не найдены
            except Status.DoesNotExist:
                pass  # Если статус не найден

    context = {
        'title': 'Мои задачи',
        'orders': orders,
        'order_items': order_items,  # Передаем только заявки текущего сотрудника
        'statuses': statuses,
        'filters': {
            'search_query': search_query,
            'status_filter': status_filter,
            'sort_order': sort_order,
        },
    }

    return render(request, 'users/staff_orders.html', context)
