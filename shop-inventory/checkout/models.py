from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone


class Order(models.Model):
    email_validator = EmailValidator(
        message="Must be a valid Rowan email address",
        allowlist=["students.rowan.edu", "rowan.edu"],
    )
    numeric_validator = RegexValidator(
        r"^\d{12}$",
        message="Must be exactly 12 numeric characters",
    )

    order_number = models.CharField(max_length=8, unique=True)
    implicit_id = models.CharField(
        max_length=255, validators=[email_validator, numeric_validator]
    )
    date = models.DateTimeField(default=timezone.now)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.order_number} ({self.implicit_id})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    inventory_item = models.ForeignKey("inventory.Inventory", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.inventory_item.base_item.name} x{self.quantity} in Order #{self.order.order_number}"
