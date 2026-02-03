from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def equipment_inventory(request):
    # Minimal implementation to allow server start
    return render(request, 'EngineerRPG/equipment_inventory.html', {})
