from django.urls import path, include
from . import views

urlpatterns = [
    path("hello", views.say_hello),
    path("create", views.create_object),
    path("update", views.update_object),
    path("delete", views.delete_object)
]
