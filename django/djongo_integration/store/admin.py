from django.contrib import admin
from . import models


class ProductAdmin(admin.ModelAdmin):
    # Shows the fields that are displayed on the admin list panel
    list_display = ["title", "unit_price", "inventory"]

    # Declares the fields that can be editable in the admin list panel
    list_editable = ["unit_price", "inventory"]

    # Declares the number of objects visible per page
    list_per_page = 10

    # def inventory_status(self, product):
    #     if product.inventory < 10:
    #         return "Low"
    #     return "OK"


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "membership"]
    list_editable = ["membership"]
    list_per_page = 10


admin.site.register(models.Collection)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Customer, CustomerAdmin)
