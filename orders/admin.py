import logging
from django.contrib import admin
from goods.models import Service
from users.models import Employee
from .models import Order, OrderItem, Status



# Регистрация модели статусов
admin.site.register(Status)


# TabularInline для строки OrderItem в Order
class OrderItemTabularAdmin(admin.TabularInline):
    model = OrderItem
    fields = ("product", "name", "price", "quantity", "status", "employee", "work_ended_datetime")
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "employee":
            # Фильтруем сотрудников по категории услуги
            parent_order_id = request.resolver_match.kwargs.get('object_id')  # Получаем ID заказа (Order)
            if parent_order_id:
                try:
                    order_items = OrderItem.objects.filter(order_id=parent_order_id)  # Получаем все связанные OrderItem
                    product_ids = order_items.values_list('product_id', flat=True)  # Список всех связанных продуктов
                    categories = Service.objects.filter(id__in=product_ids).values_list('category',
                                                                                        flat=True)  # Категории продуктов
                    kwargs["queryset"] = Employee.objects.filter(category__in=categories)  # Фильтрация сотрудников
                except Exception as e:
                    logger.error(f"Ошибка при фильтрации сотрудников: {e}")
                    kwargs["queryset"] = Employee.objects.none()
            else:
                # Для нового объекта: фильтруем по выбранному продукту
                product_id = request.POST.get('product')
                if product_id:
                    try:
                        product = Service.objects.get(id=product_id)
                        kwargs["queryset"] = Employee.objects.filter(category=product.category)
                    except Service.DoesNotExist:
                        kwargs["queryset"] = Employee.objects.none()
                else:
                    kwargs["queryset"] = Employee.objects.none()

        if db_field.name == "status":
            # Фильтруем статусы только для категории "Услуга"
            kwargs["queryset"] = Status.objects.filter(status_category="Услуга")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Админка для OrderItem
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "name", "price", "quantity", "status", "employee")
    search_fields = ("order__id", "product__name", "name")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "employee":
            # Для фильтрации сотрудников в обычной админке
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id:
                try:
                    order_item = OrderItem.objects.get(pk=obj_id)
                    kwargs["queryset"] = Employee.objects.filter(category=order_item.product.category)
                except OrderItem.DoesNotExist:
                    kwargs["queryset"] = Employee.objects.none()
            else:
                product_id = request.POST.get('product')
                if product_id:
                    try:
                        product = Service.objects.get(id=product_id)
                        kwargs["queryset"] = Employee.objects.filter(category=product.category)
                    except Service.DoesNotExist:
                        kwargs["queryset"] = Employee.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Админка для Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "requires_delivery",
        "delivery_address",
        "delivery_date",
        "delivery_time",
        "status",
        "payment_on_get",
        "is_paid",
        "created_timestamp",
    )
    search_fields = ("id", "user__username", "delivery_address")
    readonly_fields = ("created_timestamp",)
    list_filter = (
        "requires_delivery",
        "status",
        "payment_on_get",
        "is_paid",
        "delivery_date",
    )
    inlines = (OrderItemTabularAdmin,)
