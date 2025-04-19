from django.contrib import admin
from django.db.models.aggregates import Count
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.html import format_html

from . import models


class CollectionAdmin(admin.ModelAdmin):
    list_display = ["title", "collection_link", "products_count"]

    def collection_link(self, collection):
        url = (
            reverse("admin:store_product_changelist")
            + "?"
            + urlencode({"collection__pk": collection._id})
        )
        return format_html('<a href="{}">Change Products</a>', url)

    # Incompatible with Djongo
    # def products_count(self, collection):
    #     return collection.products_count

    # def get_queryset(self, request):
    #     return super().get_queryset(request).annotate(
    #         products_count=Count("product")
    #     )

    def products_count(self, collection):
        return collection.product_set.count()

    # products_count.admin_order_field = "products_count"


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

    # This decorator is incompatible with Djongo, refer to the alternative below
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


admin.site.register(models.Collection, CollectionAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Customer, CustomerAdmin)
admin.site.register(models.Order, OrderAdmin)
