from django.db import models


class Task(models.Model):
    name = models.CharField(max_length=300, null=False)
    is_completed = models.BooleanField(default=False)
    # Automatically generates the date when an instance is created
    date_created = models.DateTimeField(auto_now_add=True)
