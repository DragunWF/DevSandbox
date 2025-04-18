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
                   'tags': list(tags)})
