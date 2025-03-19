from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('registration/', views.registration, name='registration'),
    path('profile/', views.profile, name='profile'),
    path('users-cart/', views.users_cart, name='users_cart'),
    path('logout/', views.logout, name='logout'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('staff/orders/', views.staff_orders, name='staff_orders'),
    path('orders/item/<int:item_id>/toggle_picked/', views.toggle_picked_status, name='toggle_picked_status'),
    path('toggle_all_tasks_status/<int:order_id>/', views.toggle_all_tasks_status, name='toggle_all_tasks_status'),

]