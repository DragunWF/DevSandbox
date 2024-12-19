from django.db import models


class Customer(models.Model):
    MEMBERSHIP_CHOICES = [
        ("P", "Premium"),
        ("R", "Regular")
    ]

    # Note that if you want a customer primary key, you have
    # to manually pass in a keyword argument to set it as True
    # If not, Django automatically creates an ID for a data model
    id = models.CharField(max_length=10, primary_key=True)

    # Parts of the challenge
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


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    # The on_delete parameter, sets the function that will occur when the
    # Parent model (Customer) is deleted.
    # Functions include:
    # - CASCADE (Deletes the address object)
    # - SET_NULL (Sets the address to null)
    # - SET_DEFAULT (Sets the address to its default value)
    # - PROTECT (Prevent the deletion of the address object)
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        # Prevents the address from creating and ID of itself
        # Furthermore, this ensures a one-to-one relationship
        primary_key=True
    )

    # One-to-many relationship
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
