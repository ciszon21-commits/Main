
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def test_search():
    print("Testing search functionality...")
    
    # 1. Search with * (All indices)
    print("\n--- Searching '*' with empty query ---")
    resp = services.search("", indices="*")
    if "error" in resp:
        print(f"Error: {resp['error']}")
    else:
        hits = resp.get('hits', {}).get('total', {}).get('value', 0)
        print(f"Hits: {hits}")

    # 2. Search with a keyword that should exist
    # Let's try to find a keyword from the actual data if possible, but for now just test the call
    keyword = "測試" # Common Chinese word
    print(f"\n--- Searching '*' with keyword '{keyword}' ---")
    resp = services.search(keyword, indices="*")
    hits = resp.get('hits', {}).get('total', {}).get('value', 0)
    print(f"Hits: {hits}")

    # 3. Search with specific index pattern sino_early*
    print("\n--- Searching 'sino_early*' ---")
    resp = services.search("", indices="sino_early*")
    hits = resp.get('hits', {}).get('total', {}).get('value', 0)
    print(f"Hits: {hits}")
    
    # 4. Search with specific index pattern sino_early*
    print("\n--- Searching 'sino_early*' ---")
    resp = services.search("", indices="sino_early*")
    hits = resp.get('hits', {}).get('total', {}).get('value', 0)
    print(f"Hits: {hits}")

if __name__ == "__main__":
    test_search()
