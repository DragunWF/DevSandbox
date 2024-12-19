from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class LikedItem(models.Model):
    # auto_now parameter set to true
    # This makes it so the date updates everytime a user likes or unlikes an item
    date_liked_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_id = models.PositiveIntegerField()
    item_object = GenericForeignKey()
