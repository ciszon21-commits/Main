
import os
import django
from django.db.models import ProtectedError

# Setup Django environment
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from sinoVR.models import Asset3D, Scene, SceneObject, Panorama

def verify_protection():
    print("Starting verification for Asset3D deletion protection...")

    # 1. Create a dummy Asset3D
    asset = Asset3D.objects.create(title="Test Asset", file="test_asset.fbx")
    print(f"Created Asset3D: {asset.title} (ID: {asset.id})")

    # 2. Create a dummy Panorama (needed for Scene)
    pano = Panorama.objects.create(title="Test Pano", image="test_pano.jpg")

    # 3. Create a Scene
    scene = Scene.objects.create(title="Test Scene", background=pano)
    print(f"Created Scene: {scene.title} (ID: {scene.id})")

    # 4. Create a SceneObject referencing the asset
    obj = SceneObject.objects.create(scene=scene, asset=asset)
    print(f"Created SceneObject linking Asset to Scene.")

    # 5. Attempt to delete the Asset3D
    try:
        asset.delete()
        print("FAIL: Asset was deleted despite being used!")
    except ProtectedError as e:
        print("SUCCESS: Asset deletion prevented due to ProtectedError.")
        print(f"Error message details: {e}")

    # 6. Cleanup to verify successful deletion when not used
    print("Cleaning up SceneObject...")
    obj.delete()
    
    print("Attempting to delete Asset3D again...")
    asset.delete()
    print("SUCCESS: Asset deleted after references were removed.")

    # Cleanup remaining objects
    scene.delete()
    pano.delete()
    print("Verification complete.")

if __name__ == '__main__':
    verify_protection()
