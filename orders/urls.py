from django.urls import path
from orders import views

app_name = 'orders'

urlpatterns = [
    path('create-order/', views.create_order, name='create_order'),
    path('api/get-occupied-times/', views.get_occupied_times, name='get_occupied_times'),
]