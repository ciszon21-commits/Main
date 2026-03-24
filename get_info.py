import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from bgf_excavation.models import FoundationExcavation

try:
    fs = FoundationExcavation.objects.filter(bridge_id__icontains="P14N")
    for f in fs:
        print("=======", f.bridge_name, f.bridge_id, "=======")
        els = [f.el_l1_start, f.el_l1_end, f.el_l2_start, f.el_l2_end, f.el_b1_start, f.el_b1_end, f.el_b2_start, f.el_b2_end]
        print("ELs:", els)
        print("Base:", f.column_base_el)
        print("h1:", f.h1_thickness)
        print("pc:", f.c_pc_thickness)
except Exception as e:
    print("Error:", e)
