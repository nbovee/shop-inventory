from django.db import models

# Create your models here.


class base_item(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    barcode_number = models.TextField()
    active = models.BooleanField(default=True)


class location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    active = models.BooleanField(default=True)


class inventory(models.Model):
    id = models.IntegerField(primary_key=True)
    item_type = models.ForeignKey(base_item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    location = models.ManyToManyField(location, on_delete=models.CASCADE)
