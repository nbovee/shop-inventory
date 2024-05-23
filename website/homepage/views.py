from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

"""
def index(request):
    return HttpResponse("Welcome to the homepage!")
"""


def index(request):
    return render(request, "homepage.html")


def test(request):
    return HttpResponseRedirect(reverse("polls:results", args=()))
