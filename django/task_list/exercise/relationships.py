from django.db import models


class Promotion(models.Model):
    description = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=2)


class Collection(models.Model):
    title = models.CharField(max_length=255)


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=255)
    price = models.DecimalField(max_digits=10)

    # In the event that you have to pass a foreign key where the class
    # is not declared yet, you can pass in a string that matches
    # the class name instead, 'Collection'
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT)

    # Many-to-many relationship
    promotions = models.ManyToManyField(
        Promotion, 
        on_delete=models.PROTECT,
        # Django turns the argument to this parameter as the name of 
        # the key in the promotion data model
        related_name='products'
    )


class Customer(models.Model):
    MEMBERSHIP_CHOICES = [
        ("P", "Premium"),
        ("R", "Regular")
    ]
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=11)
    birth_date = models.DateField(null=True)
    membership = models.CharField(
        max_length=1,
        choices=MEMBERSHIP_CHOICES,
        default=MEMBERSHIP_CHOICES[1][0]  # Regular account
    )


class Item(models.Model):
    # Alternative for quantity: PositiveSmallIntegerField() to prevent negative values
    quantity = models.IntegerField(default=0)
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        primary_key=True
    )


class Order(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ("P", "Pending"),
        ("C", "Complete"),
        ("F", "Filled"),
    )

    placed_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=1,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_CHOICES[0][0]  # Pending
    )
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
