
import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def check_document():
    print("Fetching one document from 'sino_early'...")
    try:
        client = services.get_client()
        # Search for any document
        resp = client.search(
            index="sino_early",
            body={"size": 1, "query": {"match_all": {}}}
        )
        hits = resp.get('hits', {}).get('hits', [])
        if hits:
            doc = hits[0]
            source = doc.get('_source', {})
            print(f"\nDocument ID: {doc.get('_id')}")
            print(f"Index: {doc.get('_index')}")
            # Print structure keys
            print("Fields:", list(source.keys()))
            if 'path' in source:
                print(f"Path: {source['path']}")
            if 'file' in source:
                print(f"File: {source['file']}")
            if 'title' in source:
                print(f"Title: {source['title']}")
            
        else:
            print("No documents found in sino_early")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_document()
