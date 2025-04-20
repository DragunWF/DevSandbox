from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F, Value, Func
from django.db.models.aggregates import Count, Max, Min, Avg, Sum
from django.contrib.contenttypes.models import ContentType

from decimal import Decimal
from store.models import Product, Collection, OrderItem, Customer
from tags.models import TaggedItem


def say_hello(request):
    products = Product.objects.values()[:25]
    product_count = Product.objects.aggregate(
        count=Count("description"),
    )

    return render(request, "hello.jinja",
                  {'name': "Marc",
                   "products": products,
                   'product_count': product_count,
                   'tags': []})


def create_object(request):
    collection = Collection()
    collection.title = "Dragun Video Games"
    collection.featured_product = Product(pk=1)
    collection.save()

    return HttpResponse(f"{collection.title} has been created!")


def update_object(request):
    Collection.objects.filter(pk=11).update(featured_product=None)
    return HttpResponse("Collections have been updated!")


def delete_object(request):
    Collection.objects.filter(id__gt=5).delete()
    return HttpResponse("Object has been deleted!")
