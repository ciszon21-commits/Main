
import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def test_content_search():
    keyword = "水庫"
    print(f"--- Testing search for '{keyword}' with include_content=False (Default) ---")
    resp_default = services.search(keyword, indices="*", include_content=False)
    hits_default = resp_default.get('hits', {}).get('total', {}).get('value', 0)
    print(f"Hits: {hits_default}")

    print(f"\n--- Testing search for '{keyword}' with include_content=True ---")
    resp_content = services.search(keyword, indices="*", include_content=True)
    hits_content = resp_content.get('hits', {}).get('total', {}).get('value', 0)
    print(f"Hits: {hits_content}")

if __name__ == "__main__":
    test_content_search()
