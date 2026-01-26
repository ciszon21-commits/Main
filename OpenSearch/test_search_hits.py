
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def test_search():
    print("Testing search functionality with hit inspection...")
    
    keyword = "測試"
    print(f"\n--- Searching '*' with keyword '{keyword}' ---")
    resp = services.search(keyword, indices="*")
    
    if "error" in resp:
        print(f"Error: {resp['error']}")
        return

    hits_info = resp.get('hits', {})
    total = hits_info.get('total', {}).get('value', 0)
    hits = hits_info.get('hits', [])
    
    print(f"Total Hits: {total}")
    print(f"Returned Hits: {len(hits)}")
    
    if hits:
        first_hit = hits[0]
        print(f"\nFirst Hit Index: {first_hit.get('_index')}")
        print(f"First Hit ID: {first_hit.get('_id')}")
        print(f"First Hit Source Keys: {list(first_hit.get('_source', {}).keys())}")
        print(f"First Hit Title: {first_hit.get('_source', {}).get('title')}")
    else:
        print("No hits returned in the 'hits' list!")

if __name__ == "__main__":
    test_search()
