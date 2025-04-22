from django.contrib import admin
from .models import Product, Branch, Resort, Ratings

# Register your models here.
admin.site.register(Product)
admin.site.register(Branch)
admin.site.register(Resort)
admin.site.register(Ratings)
