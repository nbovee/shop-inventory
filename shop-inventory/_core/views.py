from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

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
