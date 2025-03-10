from django.contrib import admin

from carts.admin import CartTabAdmin
from users.models import User, Employee



# admin.site.register(Category)
admin.site.register(Employee)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'first_name', 'last_name', 'email' ]

    inlines = [CartTabAdmin]