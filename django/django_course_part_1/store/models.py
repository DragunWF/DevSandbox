from djongo import models
from django.core.validators import MinValueValidator

from bson.objectid import ObjectId


class Promotion(models.Model):
    _id = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=255)
    discount = models.FloatField()


class Collection(models.Model):
    _id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)

    # An alternate way to pass in a reference is to supply the name of the class
    # as a string instead of a class which allows you to pass in classes that get
    # get declared much later than this class (Collection)
    # Adding in "+" to related_name tells Django to not create a reverse relationship
    featured_product = models.ForeignKey("Product",
                                         on_delete=models.SET_NULL,
                                         null=True,
                                         related_name="+")

    def __str__(self) -> str:
        return self.title

    class Meta:
        # This sorts the list when viewed on the admin panel
        ordering = ["title"]


class Product(models.Model):
    _id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(
        null=True, blank=True)  # Makes this field optional
    unit_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )
    inventory = models.IntegerField(validators=[MinValueValidator(0)])

    # auto_now=True : means everytime we update this data model, it automatically stores the date in this field
    # auto_now_add=True : the date is generated only when the first time the product object is created
    last_update = models.DateTimeField(auto_now=True)

    collection = models.ForeignKey(Collection, on_delete=models.PROTECT)

    # related_name=<name> : sets the name of the field or column on the parent (Promotion) class
    promotions = models.ManyToManyField(
        Promotion, related_name="products", blank=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        ordering = ["title"]


class Customer(models.Model):
    MEMBERSHIP_BRONZE = "B"
    MEMBERSHIP_SILVER = "S"
    MEMBERSHIP_GOLD = "G"

    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, "Bronze"),
        (MEMBERSHIP_SILVER, "Silver"),
        (MEMBERSHIP_GOLD, "Gold")
    ]

    _id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=34)
    birth_date = models.DateTimeField(null=True)

    # choices=<value> : indicates the only values that the field can accept
    # It takes in a list of tuples
    # - The first item is the actual value stored in the database
    # - The second item is the human-readable name
    membership = models.CharField(max_length=1,
                                  choices=MEMBERSHIP_CHOICES,
                                  default="B")

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    # Meta data about the collection/table
    class Meta:
        ordering = ["first_name", "last_name"]
        db_table = "store_customer"
        indexes = [
            models.Index(fields=["last_name", "first_name"])
        ]


class Order(models.Model):
    PAYMENT_STATUS_PENDING = "P"
    PAYMENT_STATUS_COMPLETE = "C"
    PAYMENT_STATUS_FAILED = "F"

    PAYMENT_STATUSES = [
        (PAYMENT_STATUS_PENDING, "Pending"),
        (PAYMENT_STATUS_COMPLETE, "Complete"),
        (PAYMENT_STATUS_FAILED, "Failed")
    ]

    placed_at = models.DateField(auto_now_add=True)
    payment_status = models.CharField(max_length=1,
                                      choices=PAYMENT_STATUSES,
                                      default=PAYMENT_STATUS_PENDING)

    customer = models.ForeignKey(Customer,
                                 on_delete=models.PROTECT,
                                 primary_key=True,
                                 unique=False)


class Cart(models.Model):
    _id = models.IntegerField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    _id = models.IntegerField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()


class OrderItem(models.Model):
    _id = models.IntegerField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)


class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=4, default="0000")

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
