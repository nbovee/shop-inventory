from django.db import models


from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# Create your models here.


class User(AbstractUser):
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=150)
    email = models.EmailField(_("Rowan email address"))
    # banner_id = models.PositiveIntegerField()

    def __str__(self):
        return "{} ({})".format(self.username, self.id)

    REQUIRED_FIELDS = ["first_name", "last_name", "email"]
