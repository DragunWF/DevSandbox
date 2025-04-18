from django.urls import path, include
from . import views

urlpatterns = [
    path("hello", views.say_hello),
]
