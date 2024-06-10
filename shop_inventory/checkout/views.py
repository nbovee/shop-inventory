from django.http import HttpResponse, JsonResponse
from django.template import loader
from inventory.models import Inventory
from inventory.models import BaseItem
from inventory.models import Location
from django.shortcuts import render
from django.core import serializers
import json

# inventory.objects.create(item_name=1,quantity=2,barcode_number=39392,location=1,notes="menqie")

# Create your views here.
def index(request):
    #template = loader.get_template("checkout/index.html")
    #jsonfile = serializers.serialize("json",inventory.objects.all())
    #return HttpResponse(template.render())
   # return render(request,"checkout/index.html",{'data':jsonfile})
    inventory_data = Inventory.objects.all()
    base_item_data = BaseItem.objects.all()
    location_data = Location.objects.all()
    inventory_data_json = serializers.serialize('json',inventory_data)
    base_item_data_json = serializers.serialize('json',base_item_data)
    location_data_json = serializers.serialize('json',location_data)

    content = {
       'inventory_data': inventory_data_json,
       'base_item_data': base_item_data_json,
       'location_data': location_data_json
   }
    return render(request,"checkout/index.html",{"inventory_data":inventory_data_json,"base_item_data":base_item_data_json,"location_data":location_data_json})
  #  items = inventory.objects.all()
   # return render(request, 'checkout/index.html',{'items':items})


def checkoutComplete(request):
    template = loader.get_template("checkout/checkoutComplete.html")

    return HttpResponse(template.render())


def removeFromInventory(request):

    #is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
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

                #current_Item = base_item.objects.get(name=item)
            
            items[item] = str(items[item])
            print(items[item])


        return(JsonResponse({'itemzs': items}))
    else:
        return(HttpResponse("Request Method is not a PUT"))