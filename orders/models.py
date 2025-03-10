from django.db import models
from goods.models import Service
from users.models import User

from users.models import Employee
from goods.models import Service



class OrderitemQueryset(models.QuerySet):

    def total_price(self):
        return sum(cart.products_price() for cart in self)

    def total_quantity(self):
        if self:
            return sum(cart.quantity for cart in self)
        return 0


class Status(models.Model):
    status_name = models.CharField(max_length=150, verbose_name="Название статуса")
    status_category = models.CharField(max_length=150, null=True, verbose_name="Категория статуса (Заказ/Услуга)")
    status_description = models.CharField(max_length=150, verbose_name="Описание статуса")


    class Meta:
        db_table = "status"
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"

    def __str__(self):
        return f"Статус : {self.status_name}"

class Order(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_DEFAULT, blank=True, null=True, verbose_name="Пользователь",
                             default=None)
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания заказа")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона")
    requires_delivery = models.BooleanField(default=False, verbose_name="Требуется забрать на ремонт с адреса")
    delivery_address = models.TextField(null=True, blank=True, verbose_name="Адрес для забирания на ремонт")
    delivery_date = models.DateField(null=True, verbose_name='Дата доставки/получения на ремонт')
    delivery_time = models.TimeField(null=True, verbose_name='Время доставки/получения на ремонт')
    order_finished_datetime = models.DateTimeField(default=None, blank=True, null=True, verbose_name='Дата завершения заказа')
    payment_on_get = models.BooleanField(default=False, verbose_name="Оплата при получении")
    comment = models.TextField(null=True, blank=True, verbose_name="Комментарий клиента")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачено")
    status = models.ForeignKey(to=Status, on_delete=models.SET_DEFAULT, blank=True, null=True,default=1,  limit_choices_to={'status_category': 'Заказ'}, verbose_name="Статус заказа")

    class Meta:
        db_table = "order"
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ № {self.pk} | Покупатель {self.user.first_name} {self.user.last_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(to=Order, on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(to=Service, on_delete=models.SET_DEFAULT, null=True, verbose_name="Услуга", default=None)
    name = models.CharField(max_length=150, verbose_name="Название")
    price = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата продажи")
    status = models.ForeignKey(to=Status, on_delete=models.SET_DEFAULT, default=6, limit_choices_to={'status_category': 'Услуга'}, verbose_name="Статус услуги")

    employee = models.ForeignKey(to=Employee, on_delete=models.SET_DEFAULT, blank=True, null=True, default=None, verbose_name="Назначен сотруднику")

    work_ended_datetime = models.DateTimeField(default=None, blank=True, null=True, verbose_name='Дата и время выполнения')

    class Meta:
        db_table = "order_item"
        verbose_name = "Заказанная услуга"
        verbose_name_plural = "Заказанные услуги"

    objects = OrderitemQueryset.as_manager()

    def products_price(self):
        return round(self.price() * self.quantity, 2)

    def __str__(self):
        return f"Услуга {self.name} | Заказ № {self.order.pk}"
