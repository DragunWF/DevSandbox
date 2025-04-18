from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F, Value, Func
from django.db.models.aggregates import Count, Max, Min, Avg, Sum

from decimal import Decimal
from store.models import Product, Collection, OrderItem, Customer


def say_hello(request):
    data = Product.objects.all()
    result = Product.objects.aggregate(
        count=Count("description"),
    )

    return render(request, "hello.jinja",
                  {'name': "Marc", "products": data, 'result': result})
