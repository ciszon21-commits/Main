
import os
import sys
import json
import django
from django.db.models import ProtectedError
from django.test import RequestFactory
from django.http import JsonResponse

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from sinoVR.models import Asset3D, Scene, SceneObject, Panorama
from sinoVR.views import AssetDeleteView

def verify_api_protection():
    print("Starting API verification for Asset3D deletion protection...")

    # 1. Create a dummy Asset3D
    asset = Asset3D.objects.create(title="Test Asset API", file="test_asset_api.fbx")
    print(f"Created Asset3D: {asset.title} (ID: {asset.id})")

    # 2. Create a dummy Panorama (needed for Scene)
    pano = Panorama.objects.create(title="Test Pano API", image="test_pano_api.jpg")

    # 3. Create a Scene
    scene = Scene.objects.create(title="Test Scene API", background=pano)
    
    # 4. Create a SceneObject referencing the asset
    obj = SceneObject.objects.create(scene=scene, asset=asset)
    print(f"Created SceneObject linking Asset to Scene.")

    # 5. Simulate API Call
    factory = RequestFactory()
    request = factory.post(f'/sinoVR/api/asset/{asset.id}/delete/')
    view = AssetDeleteView.as_view()

    try:
        response = view(request, pk=asset.id)
        print(f"API Response Status Code: {response.status_code}")
        
        if response.status_code == 400:
            content = json.loads(response.content)
            print(f"API Response Content: {content}")
            if content.get('status') == 'error':
                 print("SUCCESS: API returned error as expected.")
            else:
                 print("FAIL: API did not return 'error' status.")
        elif response.status_code == 200:
             print("FAIL: API returned success (200)!")
        else:
             print(f"FAIL: Unexpected status code {response.status_code}")

    except Exception as e:
        print(f"FAIL: Unexpected exception during view execution: {e}")

    # 6. Check if asset still exists
    if Asset3D.objects.filter(id=asset.id).exists():
        print("SUCCESS: Asset still exists in database.")
    else:
        print("FAIL: Asset was deleted from database!")

    # Cleanup
    print("Cleaning up...")
    obj.delete()
    asset.delete()
    scene.delete()
    pano.delete()
    print("Verification complete.")

if __name__ == '__main__':
    verify_api_protection()
