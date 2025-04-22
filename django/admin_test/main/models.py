from djongo import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default="")
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    description = models.TextField(default="")
    location = models.CharField(max_length=255)
    zip_code = models.IntegerField(max_length=4)

    def __str__(self):
        return self.name


class Resort(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default="")

    def __str__(self):
        return self.name


class Ratings(models.Model):
    name = models.CharField(max_length=100)
    rating = models.IntegerField(
        validators=[MaxValueValidator(5), MinValueValidator(1)])
    description = models.TextField(default="")
    resort = models.CharField(max_length=10)

    def __str__(self):
        return self.name
