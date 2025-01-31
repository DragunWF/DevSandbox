from django.db import models


class Account(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=36)
    email = models.EmailField(default="test@example.com")

    # Classifies the meta data of the model
    class Meta:
        db_table = 'accounts'
        indexes = [
            models.Index(fields=['username'])
        ]


class Task(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owned_by = models.ForeignKey(Account, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['title', 'description'])
        ]
