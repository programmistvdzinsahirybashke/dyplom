from django.db import models
from django.urls import reverse


# Create your models here.
class Category(models.Model):

    class Meta:
        db_table = 'category'
        verbose_name = 'Категорию'
        verbose_name_plural = 'Категории'
        ordering = ("id",)

    category_name = models.CharField(max_length=150, unique=True, verbose_name = 'Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name = 'URL')

    def __str__(self):
        return self.category_name

# Модель для услуг
class Service(models.Model):

    class Meta:
        db_table = 'Service'
        verbose_name = 'Услугу'
        verbose_name_plural = 'Услуги'
        ordering = ("category", '-price')

    service_name = models.CharField(max_length=200, verbose_name = 'Название услуги')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name = 'ID категории')  # Связь с категорией
    service_description = models.TextField(max_length=250, blank=True, null=True, verbose_name = 'Описание')
    image = models.ImageField(upload_to='goods_images', blank=True, null=True, verbose_name='Изображение')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name = 'Стоимость')
    discount = models.DecimalField(default=0.00, max_digits=4, decimal_places=2, verbose_name='Скидка в %')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name = 'URL')


    def __str__(self):
        return f'{self.service_name} | {self.category}'

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"product_slug":self.slug})

    def display_id(self):
        return f'{self.id:05}'

    def sell_price(self):
        if self.discount:
            return round(self.price - self.price*self.discount/100, 2)
        return self.price