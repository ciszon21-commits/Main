import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()
from bgf_excavation.models import FoundationExcavation

f = FoundationExcavation.objects.filter(bridge_id='P29S').first()
if f:
    print(f"B1: {f.B1}, B2: {f.B2}, L1: {f.L1}, L2: {f.L2}")
    print(f"L1_start: {f.el_l1_start}, L1_end: {f.el_l1_end}")
    print(f"L2_start: {f.el_l2_start}, L2_end: {f.el_l2_end}")
    print(f"B1_start: {f.el_b1_start}, B1_end: {f.el_b1_end}")
    print(f"B2_start: {f.el_b2_start}, B2_end: {f.el_b2_end}")
    print(f"Skew: {f.skew_angle}")
else:
    print("P29S NOT FOUND")
