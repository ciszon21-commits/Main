
import os
import sys
import django
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from OpenSearch import services

def check_mapping():
    client = services.get_client()
    
    # List indices first to find a good candidate
    indices = client.cat.indices(format="json", index="alias_*")
    if not indices:
        print("No alias indices found.")
        return

    target_index = indices[0]['index']
    print(f"Checking mapping for index: {target_index}")
    
    mapping = client.indices.get_mapping(index=target_index)
    
    try:
        props = mapping[target_index]['mappings']['properties']
        print("Available fields:", list(props.keys()))
        
        if 'file' in props:
            print("File Mapping:", json.dumps(props['file'], indent=2))
        else:
             print("File field not found in properties.")
        
        # Check dynamic templates if any
        if 'dynamic_templates' in mapping[target_index]['mappings']:
             print("Dynamic Templates:", json.dumps(mapping[target_index]['mappings']['dynamic_templates'], indent=2))

    except Exception as e:
        print(f"Error parsing mapping: {e}")
        # print(json.dumps(mapping, indent=2))

if __name__ == "__main__":
    check_mapping()
