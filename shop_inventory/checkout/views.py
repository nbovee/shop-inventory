from django.http import HttpResponse, JsonResponse
from django.template import loader
from inventory.models import Inventory
from inventory.models import BaseItem
from inventory.models import Location
from django.shortcuts import render
from django.core import serializers
import json
from .forms import checkoutForm

# Create your views here.
def index(request):
    inventory_data = Inventory.objects.all()
    base_item_data = BaseItem.objects.all()
    location_data = Location.objects.all()
    inventory_data_json = serializers.serialize('json',inventory_data)
    base_item_data_json = serializers.serialize('json',base_item_data)
    location_data_json = serializers.serialize('json',location_data)

    if request.method == "POST" :
        print(request)
        form = checkoutForm(request.POST)
        print("check")
        print(request.POST)
        print(form.errors)
        quantity_data =json.loads(request.POST['quantity_JSON'])
        if form.is_valid():

            for key in quantity_data:
                for inventory_item in inventory_data:
                    if (inventory_item.base_item.name == key):
                        if(inventory_item.location.name == "Shop Front"):
                            print("Removed")
                            inventory_item.quantity = inventory_item.quantity - int(quantity_data[key])

                            if(inventory_item.quantity < 0):
                                inventory_item.quantity = 0

                            inventory_item.save()

            template = loader.get_template("checkout/checkoutComplete.html")

            return HttpResponse(template.render())
        else:

            return render(request,"checkout/index.html",{"inventory_data":inventory_data_json,"base_item_data":base_item_data_json,"location_data":location_data_json,'form':form})
    else:

        form = checkoutForm()
        #return render(request,"checkout/index.html",context)
        return render(request,"checkout/index.html",{"inventory_data":inventory_data_json,"base_item_data":base_item_data_json,"location_data":location_data_json,'form':form})



def checkoutComplete(request):
    template = loader.get_template("checkout/checkoutComplete.html")

    return HttpResponse(template.render())

def checkoutComplete2(request):
    return()

def removeFromInventory(request):

    inventory_data = Inventory.objects.all()
    base_item_data = BaseItem.objects.all()
    location_data = Location.objects.all()
    data = json.load(request)
    items = data.get('items')
    tempQuantity = 0
    if(request.method == 'PUT'):

        for item,quantity in items.items():
            for inventory_item in inventory_data:
                print(inventory_item.base_item.name)

                if (item == inventory_item.base_item.name):
                    tempQuantity = inventory_item.quantity -  int(quantity)
                    print(tempQuantity)
                    if (tempQuantity < 0):
                        inventory_item.quantity = 0
                        items[item] = inventory_item.quantity
                    else:
                        inventory_item.quantity = tempQuantity
                        items[item]  = inventory_item.quantity 
                    
                    inventory_item.save()
            
            items[item] = str(items[item])
            print(items[item])


        return(JsonResponse({'itemzs': items}))
    else:
        return(HttpResponse("Request Method is not a PUT"))

