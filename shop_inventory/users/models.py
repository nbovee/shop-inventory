from django.db import models


from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# Create your models here.


class CustomUser(AbstractUser):
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=150)
    email = models.EmailField(_("email address"))
    banner_id = models.PositiveIntegerField()

    def __str__(self):
        return "{} ({})".format(self.username, self.id)

    REQUIRED_FIELDS = ["first_name", "last_name", "email", "banner_id"]

# class users(models.Model):
#     id = models.IntegerField(primary_key=True)
#     rowan_id = models.CharField(max_length=30)
#     is_admin = models.BooleanField()
#     banner_id = models.IntegerField()
#     shop_eligibility = models.BooleanField()
#     notes = models.TextField()
