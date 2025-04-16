from django.db import models


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    inventory = models.IntegerField()

    # auto_now=True : means everytime we update this data model, it automatically stores the date in this field
    # auto_now_add=True : the date is generated only when the first time the product object is created
    last_update = models.DateTimeField(auto_now=True)


class Customer(models.Model):
    MEMBERSHIP_BRONZE = "B"
    MEMBERSHIP_SILVER = "S"
    MEMBERSHIP_GOLD = "G"

    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, "Bronze"),
        (MEMBERSHIP_SILVER, "Silver"),
        (MEMBERSHIP_GOLD, "Gold")
    ]

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=11)
    birth_date = models.DateTimeField(null=True)

    # choices=<value> : indicates the only values that the field can accept
    # It takes in a list of tuples
    # - The first item is the actual value stored in the database
    # - The second item is the human-readable name
    membership = models.CharField(max_length=1,
                                  choices=MEMBERSHIP_CHOICES,
                                  default="B")


class Order(models.Model):
    PAYMENT_STATUS_PENDING = "P"
    PAYMENT_STATUS_COMPLETE = "C"
    PAYMENT_STATUS_FAILED = "F"

    PAYMENT_STATUSES = [
        (PAYMENT_STATUS_PENDING, "Pending"),
        (PAYMENT_STATUS_COMPLETE, "Complete"),
        (PAYMENT_STATUS_FAILED, "Failed")
    ]

    placed_at = models.DateField(auto_add_now=True)
    payment_status = models.CharField(max_length=1,
                                      choices=PAYMENT_STATUSES,
                                      default=PAYMENT_STATUS_PENDING)


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    # ========= on_delete =========
    # on_delete=<option> : Executes when the parent of the data model (Customer) is deleted.
    # Available "on_delete" options:
    # - models.CASCADE : deletes the Address object
    # - models.SET_NULL : sets the Customer field to NULL
    # - models.SET_DEFAULT : sets the field to its default value
    # - models.PROTECT : prevents the deletion (child has to be deleted first before the parent)
    # ========= primary_key =========
    # primary_key=True : sets this field as the primary key, without it; Django automatically creates an ID field that is recognized as the primary key
    # ===============================
    customer = models.ForeignKey(Customer,
                                 on_delete=models.CASCADE,
                                 primary_key=True)
