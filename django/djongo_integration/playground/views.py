from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.conf import settings

from store.models import Product


import pymongo


def say_hello(request):
    # Your existing code
    query_set = Product.objects.all()
    print(list(query_set))

    # Direct MongoDB query
    client = pymongo.MongoClient(
        settings.DATABASES['default']['CLIENT']['host'])
    db = client[settings.DATABASES['default']['NAME']]
    # Adjust collection name based on actual naming
    collection = db['store_product']
    print("Direct MongoDB query:", list(collection.find()))

    return render(request, "hello.jinja",
                  {'name': "Marc", "products": list(query_set)})
