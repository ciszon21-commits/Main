
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
            
            # Print specific fields individually to avoid truncation
            print("\n--- Title ---")
            print(source.get('title', 'N/A'))
            
            print("\n--- Path ---")
            print(source.get('path', 'N/A'))
            
            print("\n--- File ---")
            # Limit file output size if needed, or print specific subfields
            file_data = source.get('file', {})
            print(f"Filename: {file_data.get('filename', 'N/A')}")
            print(f"Extension: {file_data.get('extension', 'N/A')}")
            
            print("\n--- Meta ---")
            print(source.get('meta', 'N/A'))
            
        else:
            print("No documents found in sino_early")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_document()
