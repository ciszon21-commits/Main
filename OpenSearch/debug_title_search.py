
import os
import sys
import django
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def debug_query(q):
    print(f"\n--- DEBUGGING QUERY: {q} ---")
    parsed = services.parse_search_query(q)
    print(f"Parsed: {parsed}")
    
    try:
        resp = services.search(q, size=3)
        print(f"Total Hits: {resp['hits']['total']['value']}")
        if resp['hits']['hits']:
            for i, hit in enumerate(resp['hits']['hits']):
                source = hit['_source']
                print(f"Hit {i+1}: {source.get('title', 'No Title')} (Score: {hit['_score']})")
        else:
            print("No hits found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_query("title:世曦")
    # Also debug a known working query for comparison
    debug_query("世曦")
