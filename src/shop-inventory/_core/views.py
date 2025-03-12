from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse

"""
def index(request):
    return HttpResponse("Welcome to the homepage!")
"""


def index(request):
    return render(request, "core/homepage.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", "index")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "core/login.html")


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
