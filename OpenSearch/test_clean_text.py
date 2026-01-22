
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def test_cleaning():
    garbled = "³æ¦ì©Î¤H­û"
    print(f"Testing clean_text with: {garbled}")
    cleaned = services.clean_text(garbled)
    print(f"Result: {cleaned}")
    
    expected = "單位或人員"
    if cleaned == expected:
        print("SUCCESS: Text cleaned correctly.")
    else:
        print(f"FAILURE: Expected '{expected}', got '{cleaned}'")

if __name__ == "__main__":
    test_cleaning()
