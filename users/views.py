from django.contrib.auth.decorators import login_required
from django.contrib import auth, messages
from django.db.models import Prefetch, Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
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
        # Параметры для поиска заказов
    order_search = request.GET.get('order_search', '')


    # Извлечение заказов пользователя
    orders = Order.objects.filter(user=request.user).prefetch_related(
        Prefetch(
            "orderitem_set",
            queryset=OrderItem.objects.select_related("product"),
        )
    ).order_by("-id")

    if order_search:
        orders = orders.filter(
            Q(id__icontains=order_search) |
            Q(status__status_name__icontains=order_search)
        )

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

    # Сортировка по дате создания заказа
    orders = orders.order_by('-created_timestamp' if sort_order == 'desc' else 'created_timestamp')

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



from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import OrderItem, Status








@login_required
def toggle_picked_status(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)

    if item.status.id == 3:
        # Меняем статус на "забрал"
        item.status = Status.objects.get(id=7)  # Замените на нужный ID
    elif item.status.id == 7:
        # Меняем статус на "не забрал"
        item.status = Status.objects.get(id=3)

    item.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))  # Перенаправление назад









from django.shortcuts import redirect
from django.contrib import messages
from orders.models import OrderItem, Status




def toggle_all_tasks_status(request, order_id):
    # Получаем заказ по ID
    order = get_object_or_404(Order, id=order_id)

    # Получаем все элементы (задачи) в заказе
    order_items = OrderItem.objects.filter(order=order)

    # Проверяем, что все задачи имеют одинаковый статус, равный либо 3, либо 7
    statuses = order_items.values_list('status__id', flat=True).distinct()

    # Если все задачи имеют одинаковый статус, и этот статус равен либо 3, либо 7
    if len(statuses) == 1 and statuses[0] in [3, 7]:
        new_status = 7 if statuses[0] == 3 else 3
        status = Status.objects.get(id=new_status)

        # Обновляем статус всех задач в заказе
        for item in order_items:
            item.status = status
            item.save()

        # Добавляем сообщение об успешном изменении статусов
        messages.success(request, f"Статусы изменены (заказ №{order_id}).")
    else:
        # Если хотя бы одна задача не имеет статус 3 или 7, выводим сообщение
        messages.warning(request, f"Статусы не изменены (заказ №{order_id}). У всех задач должен быть статус 'Выполнено' или 'Выдан'.")

    # Перенаправляем обратно на страницу, с которой был запрос
    return redirect(request.META.get("HTTP_REFERER", "/"))






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


from django.shortcuts import render
from django.views import View
from django.db.models import Count, Sum

from datetime import timedelta
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count, Sum, F
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Count, Sum, F
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate  # Для обрезки времени
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate  # Для обрезки времени
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Sum
from django.db.models.functions import TruncDate
from django.db.models import F, Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from django.db.models import Count, Sum, F, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from calendar import monthrange
from users.models import User
from goods.models import Service


from django.db.models import Count, F, Sum, Avg
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from calendar import monthrange
from datetime import timedelta
from users.models import User, Employee
from goods.models import Service
from django.db.models import F, Count, Sum, Avg
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, fields
from django.db.models.functions import Now
from calendar import monthrange
from datetime import timedelta
from django.db.models.functions import TruncDate


def create_report(request):
    selected_month = int(request.GET.get('month', timezone.now().month))
    selected_year = int(request.GET.get('year', timezone.now().year))

    # Количество заказов по статусам (только статусы категории "Заказ")
    orders_by_status = Order.objects.filter(
        status__status_category='Заказ',
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).values("status__status_name").annotate(count=Count("id")).order_by(
        'status__status_name')  # Группировка и сортировка по статусу

    # Итого для заказов
    total_orders_count = sum(item['count'] for item in orders_by_status)

    # Количество услуг по статусам (только статусы категории "Услуга")
    services_by_status = OrderItem.objects.filter(
        status__status_category='Услуга',
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).values("status__status_name").annotate(count=Count("id")).order_by(
        'status__status_name')  # Группировка и сортировка по статусу

    # Итого для услуг
    total_services_count = sum(item['count'] for item in services_by_status)

    # Добавляем строку "Итого"
    orders_by_status = list(orders_by_status) + [{'status__status_name': 'Итого', 'count': total_orders_count}]
    services_by_status = list(services_by_status) + [{'status__status_name': 'Итого', 'count': total_services_count}]

    # Выручка по дням
    revenue_by_date = OrderItem.objects.annotate(
        total_price=F('price') * F('quantity'),
        created_date=TruncDate('created_timestamp')
    ).filter(
        created_date__year=selected_year,
        created_date__month=selected_month
    ).values('created_date').annotate(
        total_revenue=Sum('total_price'),
        total_services=Count('id')
    ).order_by('created_date')

    # Генерация всех дней месяца
    start_date = timezone.datetime(selected_year, selected_month, 1).date()
    end_date = timezone.datetime(selected_year, selected_month, monthrange(selected_year, selected_month)[1]).date()

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    revenue_dict = {item['created_date']: item for item in revenue_by_date}

    revenue_by_date = [
        {
            'date': date.strftime('%Y-%m-%d'),
            'total_revenue': revenue_dict.get(date, {}).get('total_revenue', 0) or 0,
            'total_services': revenue_dict.get(date, {}).get('total_services', 0) or 0
        }
        for date in date_range
    ]

    # Итоговые суммы
    total_services_count = sum(item['total_services'] for item in revenue_by_date)
    total_revenue = sum(item['total_revenue'] for item in revenue_by_date)

    # Средний чек (общая сумма заказов / количество заказов)
    total_orders = Order.objects.filter(
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).count()

    # Средний чек: если есть заказы, считаем средний чек по общей выручке за месяц
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Самая популярная услуга (используем service_name вместо name)
    most_popular_service = OrderItem.objects.filter(
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).values(
        'product__service_name',
        'product__category__category_name' # Исправлено с name на service_name
    ).annotate(
        count=Count('id')
    ).order_by('-count').first()

    # Самый загруженный день
    busiest_day = Order.objects.annotate(
        day=TruncDate('created_timestamp')
    ).filter(
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).values('day').annotate(
        count=Count('id')
    ).order_by('-count').first()
    busiest_day = busiest_day['day'].strftime('%Y-%m-%d') if busiest_day else 'Нет данных'

    # Процент выполненных заказов
    completed_orders = Order.objects.filter(
        status__status_name='Завершено',
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).count()

    completed_orders_percentage = round((completed_orders / total_orders) * 100, 2) if total_orders > 0 else 0

    # Количество новых клиентов за месяц
    new_customers_count = User.objects.filter(
        date_joined__year=selected_year,
        date_joined__month=selected_month
    ).count()

    # Среднее время выполнения заказа
    completed_orders_with_time = Order.objects.exclude(order_finished_datetime=None).filter(
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    )

    # Рассчитываем среднее время выполнения
    # Фильтрация завершенных заказов в выбранный месяц и год
    # Фильтрация заказов по месяц и год
    order_items_with_time = OrderItem.objects.filter(
        work_ended_datetime__isnull=False,  # Проверяем, что время завершения работы есть
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    )

    # Вычисление разницы между временем начала работы и временем завершения
    order_items_with_time = order_items_with_time.annotate(
        completion_time=ExpressionWrapper(
            F('work_ended_datetime') - F('created_timestamp'),
            output_field=fields.DurationField()
        )
    )

    # Среднее время выполнения работы
    avg_work_time = order_items_with_time.aggregate(
        avg_time=Avg('completion_time')
    )['avg_time']

    # Преобразование в часы (если avg_time не пустое)
    if avg_work_time:
        avg_work_time_in_hours = avg_work_time.total_seconds() / 3600
    else:
        avg_work_time_in_hours = 0

    # Доля повторных заказов
    customers_with_orders = Order.objects.filter(
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).values('user').annotate(order_count=Count('id'))
    repeat_customers = customers_with_orders.filter(order_count__gt=1).count()
    repeat_order_percentage = round((repeat_customers / customers_with_orders.count()) * 100,
                                    2) if customers_with_orders.exists() else 0

    # Выручка по категориям услуг (используем category_name вместо name)
    revenue_by_category = OrderItem.objects.filter(
        created_timestamp__year=selected_year,
        created_timestamp__month=selected_month
    ).values(
        'product__category__category_name'  # Исправлено с name на category_name
    ).annotate(
        revenue=Sum(F('price') * F('quantity'))
    ).order_by('-revenue')

    # Список месяцев
    months = [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]
    current_year = timezone.now().year

    context = {
        "orders_by_status": list(orders_by_status),
        "services_by_status": list(services_by_status),
        "revenue_by_date": revenue_by_date,
        "total_revenue": total_revenue,
        "total_services_count": total_services_count,
        "total_revenue_month": total_revenue,
        "months": months,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "current_year": current_year,
        "avg_order_value": round(avg_order_value, 2),
        "most_popular_service": most_popular_service,
        "busiest_day": busiest_day,
        "completed_orders_percentage": completed_orders_percentage,
        "new_customers_count": new_customers_count,
        "avg_order_completion_time": round(avg_work_time_in_hours, 2),
        "repeat_order_percentage": repeat_order_percentage,
        "revenue_by_category": list(revenue_by_category),
    }

    return render(request, 'users/reports.html', context)
