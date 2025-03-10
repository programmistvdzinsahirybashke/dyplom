from django.contrib import admin

from carts.models import Cart

# Register your models here.
class CartTabAdmin(admin.TabularInline):
    model = Cart
    fields = "product", "quantity", "created_timestamp"
    search_fields = "product", "quantity", "created_timestamp"
    readonly_fields = ("created_timestamp",)
    extra = 1

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'product', 'quantity', 'created_timestamp' ]
    list_filter = ['product__service_name', 'product__category', 'user', 'created_timestamp' ]

    def user_display(self, obj):
        if obj.user:
            return str(obj.user)
        return "Анонимный пользователь"

    # user_display and product_display alter name of columns in admin panel
    user_display.short_description = "Пользователь"
