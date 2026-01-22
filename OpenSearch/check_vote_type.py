
import os
import sys
import django
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def check_vote():
    client = services.get_client()
    try:
        # Check mapping for sino_early (which likely has the schema)
        m = client.indices.get_mapping(index='sino_early')
        props = m['sino_early']['mappings']['properties']
        if 'vote' in props:
            print(f"Vote field type: {props['vote']}")
        else:
            print("Vote field not found in mapping")
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_vote()
