
import os
import sys
import django
import json

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def check_mapping():
    print("Checking mappings for 'sino_early'...")
    try:
        client = services.get_client()
        mapping = client.indices.get_mapping(index="sino_early")
        
        for idx_name, data in mapping.items():
            props = data.get('mappings', {}).get('properties', {})
            print(f"\nIndex: {idx_name}")
            print("Fields found:", sorted(list(props.keys())))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_mapping()
