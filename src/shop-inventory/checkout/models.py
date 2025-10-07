from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


def validate_email_or_numeric(value):
    """Validate that the value is either a Rowan email or a 12-digit number."""
    email_regex = r"^[a-zA-Z0-9._%+-]+@(students\.rowan\.edu|rowan\.edu)$"
    email_validator = RegexValidator(
        email_regex,
        message="Must be a valid Rowan email address (@students.rowan.edu or @rowan.edu)",
    )
    numeric_validator = RegexValidator(
        r"^\d{12}$",
        message="Must be exactly 12 numeric characters",
    )

    # Try both validators
    email_valid = True
    numeric_valid = True

    try:
        email_validator(value)
    except ValidationError:
        email_valid = False

    try:
        numeric_validator(value)
    except ValidationError:
        numeric_valid = False

    # If neither validation passed, raise error
    if not email_valid and not numeric_valid:
        raise ValidationError(
            "ID field must be either a valid Rowan email address or RowanCard"
        )


class Order(models.Model):
    order_number = models.CharField(max_length=8, unique=True)
    implicit_id = models.CharField(
        max_length=255,
        validators=[validate_email_or_numeric],
        help_text="Enter either your Rowan email or 12-digit ID",
    )
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.order_number} ({self.implicit_id})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    inventory_item = models.ForeignKey("inventory.Inventory", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.inventory_item.product.name} x{self.quantity} in Order #{self.order.order_number}"
