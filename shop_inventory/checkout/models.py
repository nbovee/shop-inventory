from django.db import models


# Create your models here.
class orders(models.Model):
    id = models.IntegerField(primary_key=True)
    # users = models.ForeignKey(users, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    stuff = models.ManyToManyField("inventory")
    feedback = models.TextField()
    notes = models.TextField()
    requests = models.TextField()
