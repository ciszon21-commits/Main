
import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def test_keyword_search():
    keywords = ["水庫", "捷運"]
    
    for kw in keywords:
        print(f"\n--- Testing search for keyword: '{kw}' ---")
        try:
            resp = services.search(kw, indices="*")
            if "error" in resp:
                print(f"Error: {resp['error']}")
                continue
                
            hits = resp.get('hits', {})
            total = hits.get('total', {}).get('value', 0)
            print(f"Total Hits: {total}")
            
            if total > 0:
                print("First hit source keys:", hits.get('hits', [])[0].get('_source', {}).keys())
            
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_keyword_search()
