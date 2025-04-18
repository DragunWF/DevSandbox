from django.shortcuts import render
from django.http import HttpResponse
from store.models import Product


def say_hello(request):
    # This returns a manager object which acts as an interface to the database
    # Calling the .all() method will return a query set
    query_set = Product.objects.all()

    for product in query_set:
        print(product)

    return render(request, "hello.html", {'name': "Marc"})
