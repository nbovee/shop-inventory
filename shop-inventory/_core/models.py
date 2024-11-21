from django.db import models


from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    username = models.CharField(_("username"), max_length=150, unique=True)
    password = models.CharField(_("password"), max_length=128)

    def __str__(self):
        return "{} ({})".format(self.username, self.id)
