from django.shortcuts import render
from django.http import HttpResponse
from models import Account, Task

# Create your views here.


def say_hello(request):
    # The 'objects' part of the Account returns a Manager object
    # that is used as an interface for the database. It has several
    # different methods to query objects. Furthermore, you can also
    # chain them. Example: query_set.filter().filter().order_by()
    query_set = Account.objects.all()
    return str(list(query_set))
