from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class CustomLoginForm(AuthenticationForm):
    """
    Custom authentication form that extends Django's AuthenticationForm.
    Adds username whitespace stripping and custom error messages.
    """

    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        ),
        strip=True,  # This automatically strips whitespace
    )

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )

    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
    }
