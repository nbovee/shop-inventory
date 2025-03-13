from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse
from django.contrib import messages
from .forms import CustomLoginForm

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
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Success</title>
    </head>
    <body>
        Success
    </body>
    </html>
    """
    return HttpResponse(html, content_type="text/html")
