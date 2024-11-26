from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator, RegexValidator

# Create your models here.


class Order(models.Model):
    email_validator = EmailValidator(
        message="Must be a valid Rowan email address",
        allowlist=["students.rowan.edu", "rowan.edu"],
    )
    numeric_validator = RegexValidator(
        r"^\d{12}$",
        message="Must be exactly 12 numeric characters",
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    items = models.ManyToManyField("inventory.Inventory", through="OrderItem")
    completed = models.BooleanField(default=False)
    implicit_id = models.CharField(
        max_length=255, validators=[email_validator, numeric_validator]
    )

    @transaction.atomic
    def process_order(self):
        order = Order.objects.create(user=self.user)
        for item in self.items.all():
            OrderItem.objects.create(
                order=order, product=item.product, quantity=item.quantity
            )
            item.product.quantity -= item.quantity
            item.product.save()
        self.items.all().delete()
        order.completed = True


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey("inventory.Inventory", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
