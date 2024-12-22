from django.shortcuts import render
from django.http import HttpResponse
from .models import Account, Task

# Create your views here.


def hello(request):
    # The 'objects' part of the Account returns a Manager object
    # that is used as an interface for the database. It has several
    # different methods to query objects. Furthermore, you can also
    # chain them. Example: query_set.filter().filter().order_by()

    # Other methods include get(pk=1) which grabs the row with the
    # matching primary key. Alternatively, the keyword parameter name
    # can be the name of a column in the database like "username",
    # "email", and others.

    query_set = Account.objects.all()
    print(list(query_set))
    return HttpResponse(str(list([obj.username for obj in query_set])))
