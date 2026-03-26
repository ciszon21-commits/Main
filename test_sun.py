import os
import django
import sys

# Setup Django environment
sys.path.append('e:/00.DEVE/01.VibeCoding/CodevStudio')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from LumaSite.services import SunPositionService
from django.utils import timezone

def test_sun_position():
    lat, lng = 25.04, 121.51 # Taipei
    # Summer Solstice Noon
    dt = timezone.make_aware(timezone.datetime(2024, 6, 21, 12, 0, 0))
    
    azimuth, elevation = SunPositionService.get_sun_position(lat, lng, dt)
    print(f"Time: {dt}")
    print(f"Azimuth: {azimuth:.2f}")
    print(f"Elevation: {elevation:.2f}")
    
    if 80 < elevation < 90:
        print("✅ Elevation looks correct for summer noon in Taipei.")
    else:
        print("❌ Elevation seems off.")

if __name__ == "__main__":
    test_sun_position()
