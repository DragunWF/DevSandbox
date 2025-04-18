from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, F

from store.models import Product, Collection, OrderItem


def say_hello(request):
    data = Product.objects.all()

    return render(request, "hello.jinja",
                  {'name': "Marc", "products": data})
