import os
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.utils.skill_layout import calculate_layout_data

def verify_layout():
    # Only for CIVIL warrior
    layout = calculate_layout_data('CIVIL')
    
    # Target nodes
    # 環景攝影技術 (ID: 13)
    # 3D 點雲處理技術 (ID: 10)
    # VR虛擬實境訓練 (ID: 36)
    
    print("Verification Results for CIVIL (Supervision Group Adjacency):")
    for item in layout:
        if item['name'] in ['監造行政作業基礎', '監造權責與倫理', '工程法規概論']:
            print(f"{item['name']} (ID: {item['id']}): X={item['position_x']}, Y={item['position_y']}")

if __name__ == "__main__":
    verify_layout()
