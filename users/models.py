from django.contrib.auth.models import AbstractUser
from django.db import models

from goods.models import Category


# Create your models here.
class User(AbstractUser):
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    image = models.ImageField(upload_to='users_image', blank=True, null=True, verbose_name='Аватар')

# Модель Employee
class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')

    class Meta:
        db_table = 'employee'
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ("id",)

    def __str__(self):
        return f"{self.user.username} - {self.category.category_name}"