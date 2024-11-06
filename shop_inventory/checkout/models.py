from django.db import models, transaction
from django.contrib.auth import get_user_model


# Create your models here.


class Order(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    items = models.ManyToManyField("inventory.Inventory", through="OrderItem")
    completed = models.BooleanField(default=False)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey("inventory.Inventory", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Cart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # TODO form validator that checks an email is added?
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


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("inventory.inventory", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
