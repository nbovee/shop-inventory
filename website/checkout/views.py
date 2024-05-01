from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
# Create your views here.
def index(request):
    template = loader.get_template('checkout/index.html')

    return HttpResponse(template.render())

def checkoutComplete(request):
    template = loader.get_template('checkout/checkoutComplete.html')

    return HttpResponse(template.render())


