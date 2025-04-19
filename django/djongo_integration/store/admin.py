from django.contrib import admin
from . import models


class ProductAdmin(admin.ModelAdmin):
    # Shows the fields that are displayed on the admin list panel
    list_display = ["title", "unit_price",
                    "inventory_status", "collection_title"]

    # Declares the fields that can be editable in the admin list panel
    list_editable = ["unit_price"]

    # Declares the number of objects visible per page
    list_per_page = 10

    # A way of showing the attributes of another related object
    def collection_title(self, product):
        return product.collection.title

    # @admin.display(ordering="inventory")
    def inventory_status(self, product):
        if product.inventory < 10:
            return "Low"
        return "OK"

    inventory_status.short_description = "Inventory Status"
    inventory_status.admin_order_field = "inventory"


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "membership"]
    list_editable = ["membership"]
    list_per_page = 10


class OrderAdmin(admin.ModelAdmin):
    list_display = ["customer", "placed_at", "payment_status"]
    list_editable = ["payment_status"]


admin.site.register(models.Collection)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Customer, CustomerAdmin)
admin.site.register(models.Order, OrderAdmin)
