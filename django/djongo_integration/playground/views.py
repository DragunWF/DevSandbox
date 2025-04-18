from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from store.models import Product


def say_hello(request):
    # Your existing code
    query_set = Product.objects.filter(
        Q(inventory__lt=10) | Q(unit_price__lt=20))

    return render(request, "hello.jinja",
                  {'name': "Marc", "products": list(query_set)})
