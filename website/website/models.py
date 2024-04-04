from django.db import models


class users(models.Model):
    id = models.IntegerField(primary_key=True)
    rowan_id = models.CharField(max_length=30)
    is_admin = models.BooleanField()
    banner_id = models.IntegerField()
    shop_eligibility = models.BooleanField()
    notes = models.TextField()

class orders(models.Model):
    id = models.IntegerField(primary_key=True)
    users = models.CharField(max_length=30)
    timestamp = models.DateTimeField()
    orange = models.IntegerField()
    apple = models.IntegerField()
    soup = models.IntegerField()
    kcup = models.IntegerField()
    feedback = models.TextField()
    notes = models.TextField()
    requests = models.TextField()

class locations(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    active = models.BooleanField()

class inventory(models.Model):
    id = models.IntegerField(primary_key=True)
    item_name = models.TextField()
    quantity = models.IntegerField()
    barcode_number = models.TextField()
    notes = models.TextField()