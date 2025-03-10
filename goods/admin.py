from django.contrib import admin
from goods.models import Category, Service

# admin.site.register(Category)
# admin.site.register(Service)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name', )}
    list_display = ['category_name', 'slug', ]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('service_name', )}
    list_display = ['service_name', 'category', 'price', 'discount',]
    list_editable = ['discount',]
    search_fields = ['service_name', 'service_description']
    list_filter = ['service_name', 'category', 'price', 'discount']