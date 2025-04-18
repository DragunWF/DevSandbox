from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F

from store.models import Product, Collection, OrderItem


def say_hello(request):
    order_items = [item[0]
                   for item in OrderItem.objects.values_list("product")]
    products = list(Product.objects.values())
    ordered_products = []
    assign_ids(products)
    for product in products:
        if product["id"] in order_items:
            ordered_products.append(product)
    ordered_products.sort(key=lambda product: product["title"])

    return render(request, "hello.jinja",
                  {'name': "Marc", "products": ordered_products})


def assign_ids(data_set):
    for i, item in enumerate(data_set):
        item["id"] = i + 1
