import pytest
from django.contrib.auth.models import User
from orders.models import Order, Service, Status


@pytest.mark.django_db
def test_order_calculate_total_cost():
    # Создаем тестового пользователя
    user = User.objects.create_user(username="test_user", password="password123")

    # Создаем тестовую услугу
    service = Service.objects.create(name="Repair Wheels", price=50)

    # Создаем тестовый статус
    status = Status.objects.create(name="Pending")

    # Создаем заказ
    order = Order.objects.create(
        customer=user,
        service=service,
        status=status,
    )

    # Проверяем расчет стоимости
    order.calculate_total_cost()
    assert order.total_cost == service.price, "Стоимость заказа должна совпадать со стоимостью услуги"

import pytest
from goods.models import Category

@pytest.mark.django_db
def test_category_creation():
    # Создаем категорию
    category = Category.objects.create(
        name="Electric Scooters",
        description="Repairs and maintenance for electric scooters."
    )

    # Проверяем, что объект создан
    assert Category.objects.count() == 1, "Category object should be created in the database."

    # Проверяем значения полей
    assert category.name == "Electric Scooters", "Category name should match the input."
    assert category.description == "Repairs and maintenance for electric scooters.", \
        "Category description should match the input."
