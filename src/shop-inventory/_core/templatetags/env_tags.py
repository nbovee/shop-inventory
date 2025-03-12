from django import template
import os

register = template.Library()


@register.simple_tag
def get_env_var(var_name):
    """Returns an environment variable value"""
    return os.getenv(var_name, var_name)
