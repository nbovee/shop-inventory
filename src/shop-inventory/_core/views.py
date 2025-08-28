from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import CustomLoginForm


# Custom group_required decorator for project-wide use
def group_required(*group_names):
    """
    Decorator that checks if a user is in at least one of the specified groups.
    Usage: @group_required('admin', 'staff')
    """

    def check_group(user):
        if user.is_authenticated:
            if user.is_superuser:
                return True
            return user.groups.filter(name__in=group_names).exists()
        return False

    return user_passes_test(check_group, login_url="login")


"""
def index(request):
    return HttpResponse("Welcome to the homepage!")
"""


def index(request):
    return render(request, "core/homepage.html")


def user_login(request):
    # Get the next URL or default to index
    next_url = request.GET.get("next", "index")

    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            # Explicitly authenticate the user
            user = authenticate(username=username, password=password)

            if user is not None and user.is_active:
                login(request, user)
                messages.success(
                    request, f"Welcome, {username}! You have successfully logged in."
                )
                return redirect(next_url)
        messages.error(request, "Invalid login credentials.")
    else:
        form = CustomLoginForm(request)

    return render(request, "core/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("index")


def captive_portal_detect(request):
    """
    Handle iOS/iPadOS captive portal detection requests.
    Returns a success page that indicates the device is connected to the internet.
    Also handles manual navigation to hotspot-detect.html by redirecting to main app.
    """
    # Check if this is an automated captive portal check vs manual navigation
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    if 'CaptiveNetworkSupport' in user_agent:
        # Automated iOS/macOS check - return minimal success page
        html = """<!DOCTYPE html><html><head><title>Success</title><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>Success</body></html>"""
        return HttpResponse(html, content_type="text/html")
    else:
        # Manual navigation - redirect to main application
        return redirect("index")
